# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
# Author: Olivier Grisel <ogrisel@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#

#$Id$

# testing module and harness


from DateTime import DateTime
from OFS.Image import File
from cStringIO import StringIO
from itertools import chain
import lxml.etree
import os
import shutil
import tempfile
import unittest

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.CatalogTool import CatalogTool
from Products.CPSCourrier.tests.layer import IntegrationTestCase
from Products.CPSCourrier.workflows.scripts import reply_to_incoming
from Products.CPSCourrier.relations import make_reply_to
from Products.CPSCourrier.config import (
    RELATION_GRAPH_ID, IS_REPLY_TO, HAS_REPLY)


# import things to test
from Products.CPSCourrier.archive import Archiver

def _batching_call(self, *args, **kw):
    """Patch for the ZCatalog __call__ to fake a Lucene catalog"""
    b_start = kw.pop('b_start', None)
    b_size = kw.pop('b_size', None)
    results = list(self._original_call(*args, **kw))

    if b_start is None:
        return results

    if b_size is None:
        b_size = len(results)

    return results[b_start:b_start+b_size]


class ArchiverIntegrationTestCase(IntegrationTestCase):

    def afterSetUp(self):
        # patch the catalog to add fake batching support a la lucene
        CatalogTool._original_call = CatalogTool.__call__
        CatalogTool.__call__ = _batching_call

        # create an archiver instance
        self.tmp_archive_dir = tempfile.mkdtemp()
        self.archiver = Archiver(self.portal, archive_home=self.tmp_archive_dir)
        # use the 'ExpirationDate' field instead of the 'ModificationDate' to
        # simplify the test fixture
        self.archiver.date_field_id = "ExpirationDate"

        self.login('manager')
        IntegrationTestCase.fixtureSetUp(self)

        # add some incoming mails and replies to them
        self.wtool = getToolByName(self.portal, 'portal_workflow')
        self.incoming_mails = []
        self.outgoing_mails = []

        # 5 incoming mails
        for i in range(5):
            mail_id = 'in_mail%d' % i
            mail_data = {
                'Title': 'Test mail %d' % i,
                'mail_to': ['foo@foo.com'],
                'mail_from': 'bar@foo.com',
                self.archiver.date_field_id: DateTime(),
            }
            self.wftool.invokeFactoryFor(self.mb, 'Incoming Mail', mail_id,
                                         **mail_data)
            in_mail = self.mb[mail_id]
            self.incoming_mails.append(in_mail)
            self.wtool.doActionFor(in_mail, 'handle')
            # two outoing replies for each incoming mail
            doc_def = {self.archiver.date_field_id: DateTime()}
            for _ in range(2):
                out_mail = reply_to_incoming(in_mail)
                self.outgoing_mails.append(out_mail)
                doc = out_mail.getEditableContent()
                # attach files to the outgoing mail
                ti = doc.getTypeInfo()
                ti.flexibleAddWidget(doc, 'mail_flexible', 'file')
                ti.flexibleAddWidget(doc, 'mail_flexible', 'file')
                doc_def.update({
                    'file_f0': File('file_f0', 'some_file.txt' ,
                                    StringIO('This is a test')),
                    'file_1_f0': File('file_1_f0', 'other_file.txt',
                                      StringIO('Other test content'))
                })
                doc.edit(doc_def, out_mail)

        # link incoming #1 as a reply of outgoing #1 to get a bigger thread:
        # - in0
        #    - out0
        #    - out1
        #       - in1
        #          - out2
        #          - out3
        make_reply_to(self.incoming_mails[1], self.outgoing_mails[1])

    def beforeTearDown(self):
        # unpatch the catalog
        CatalogTool.__call__ = CatalogTool._original_call
        delattr(CatalogTool, '_original_call')

        # clean temp dir
        shutil.rmtree(self.tmp_archive_dir)
        #print '#' * 80
        #print 'archive directory:', self.tmp_archive_dir

        # ensure the catalog is clean
        self.portal.portal_catalog.refreshCatalog(clear=1)

        # ensure the graph is clean
        for mail in chain(self.incoming_mails, self.outgoing_mails):
            self.portal.portal_relations.removeAllRelationsFor(
                RELATION_GRAPH_ID, int(mail.getDocid()))
        # delete the test areas
        self.portal.mailboxes.manage_delObjects([self.MBG_ID])
        self.incoming_mails = []
        self.logout()

    def _putMailInPast(self, mail, days):
        """Helper method to change the creation date of a mail"""
        doc = mail.getEditableContent()
        fid = self.archiver.date_field_id
        doc.edit({fid: doc.getDataModel()[fid] - days}, mail)

    def _sortedRpaths(self, proxies):
        """Function to help compare list of proxies"""
        rpath = getToolByName(self.portal, 'portal_url').getRpath
        return sorted(rpath(m) for m in proxies)

    def test_getThreadsToArchive(self):
        # by default, no mail is in a state that deserves archiving
        results = list(self.archiver.getThreadsToArchive())
        self.assertEquals(results, [])

        # make almost all of the first thread archivable (right creation time
        # and review states
        for mail in self.incoming_mails[:2]: # 0 to 1
            self._set_state(mail, 'closed')
            self._putMailInPast(mail, 300)
        for mail in self.outgoing_mails[:3]: # 0 to 2
            self._set_state(mail, 'sent')
            self._putMailInPast(mail, 500)
        results = list(self.archiver.getThreadsToArchive())
        self.assertEquals(results, [])

        # setting the creation date of the last outgoing mail of the first
        # thread is not enough either
        self._putMailInPast(self.outgoing_mails[3], 200)
        results = list(self.archiver.getThreadsToArchive())
        self.assertEquals(results, [])

        # setting it in the right state makes the first thread ready for
        # archiving
        self._set_state(self.outgoing_mails[3], 'sent')
        self._putMailInPast(self.outgoing_mails[3], 200) # needed to reindex

        threads = list(self.archiver.getThreadsToArchive())
        self.assertEquals(len(threads), 1)

        result0 = self._sortedRpaths(threads[0])
        expected0 = self._sortedRpaths(self.incoming_mails[:2]
                                       + self.outgoing_mails[:4])
        self.assertEquals(result0, expected0)

        # making another thread available for archiving
        mail = self.incoming_mails[3]
        self._set_state(mail, 'trash')
        self._putMailInPast(mail, 300)
        for mail in self.outgoing_mails[6:]: # 6 to 9
            self._set_state(mail, 'sent')
            self._putMailInPast(mail, 500)

        threads = list(self.archiver.getThreadsToArchive())
        self.assertEquals(len(threads), 2)

        result0 = self._sortedRpaths(threads[0])
        self.assertEquals(result0, expected0) # same as previously

        result1 = self._sortedRpaths(threads[1])
        expected1 = self._sortedRpaths([self.incoming_mails[3]]
                                       + self.outgoing_mails[6:8])
        self.assertEquals(result1, expected1)

    def test_exportProxyToXml(self):
        # archiving an incoming mail
        self.archiver.exportProxyToXml(self.incoming_mails[0])
        filename = "mailboxes/test-mailbox-group/test-mailbox/in_mail0.xml"
        tree = lxml.etree.parse(os.path.join(self.tmp_archive_dir, filename))
        object = tree.xpath('/object')[0]
        self.assertEquals(object.get('portal_type'), 'Incoming Mail')
        title = tree.xpath("//f[@id='Title']")[0]
        self.assertEquals(title.get('v'), 'Test mail 0')

        #TODO: test docid, wf history, relations

        # archiving an outgoing mail
        self.archiver.exportProxyToXml(self.outgoing_mails[0])
        filename = ("mailboxes/test-mailbox-group/test-mailbox/"
                    "re-test-mail-0.xml")
        tree = lxml.etree.parse(os.path.join(self.tmp_archive_dir, filename))
        object = tree.xpath('/object')[0]
        self.assertEquals(object.get('portal_type'), 'Outgoing Mail')
        title = tree.xpath("//f[@id='Title']")[0]
        self.assertEquals(title.get('v'), 'Re: Test mail 0')

        #TODO: test docid, wf history, relations

    def test_archive(self):
        # make 2 threads archivable as previously
        in_mails = [(i, self.incoming_mails[i]) for i in (0, 1, 3)]
        for _, mail in in_mails:
            self._set_state(mail, 'closed')
            self._putMailInPast(mail, 300)
        out_mails = [(i, self.outgoing_mails[i]) for i in range(4)+range(6, 8)]
        for _, mail in out_mails:
            self._set_state(mail, 'sent')
            self._putMailInPast(mail, 500)

        # archive them
        self.archiver.archive()

        # check they are archived:
        path_pattern = "mailboxes/test-mailbox-group/test-mailbox/%s.xml"

        for i, mail in in_mails:
            filename = path_pattern % mail.getId()
            filepath = os.path.join(self.tmp_archive_dir, filename)
            tree = lxml.etree.parse(filepath)
            object = tree.xpath('/object')[0]
            self.assertEquals(object.get('portal_type'), 'Incoming Mail')
            title = tree.xpath("//f[@id='Title']")[0]
            self.assertEquals(title.get('v'), 'Test mail %d' % i)

        for i, mail in out_mails:
            filename = path_pattern % mail.getId()
            filepath = os.path.join(self.tmp_archive_dir, filename)
            tree = lxml.etree.parse(filepath)
            object = tree.xpath('/object')[0]
            self.assertEquals(object.get('portal_type'), 'Outgoing Mail')
            title = tree.xpath("//f[@id='Title']")[0]
            self.assertEquals(title.get('v'), 'Re: Test mail %d' % (i / 2))

        # check they are all deleted:
        archived_ids = set(m.getId() for _, m in in_mails + out_mails)
        remaining_ids = set(self.mb.objectIds())
        self.assertEquals(archived_ids & remaining_ids, set())

        # check that the remaining mails were not archived:
        all_ids = set(m.getId() for m in self.incoming_mails +
                                         self.outgoing_mails)
        self.assertEquals(remaining_ids, all_ids - archived_ids)

        # check that the relation tool no longer have reference to archived
        # mails:
        rtool = getToolByName(self.portal, 'portal_relations')
        g = rtool.getGraph(RELATION_GRAPH_ID)
        for _, mail in in_mails + out_mails:
            references = g.getRelationsFor(int(mail.getDocid()), IS_REPLY_TO)
            self.assertEquals(references, ())
            replies = g.getRelationsFor(int(mail.getDocid()), HAS_REPLY)
            self.assertEquals(replies, ())


def test_suite():
    return unittest.makeSuite(ArchiverIntegrationTestCase)
