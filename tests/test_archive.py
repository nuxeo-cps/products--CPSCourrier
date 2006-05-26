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

import unittest
from itertools import chain
from DateTime import DateTime

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.CatalogTool import CatalogTool
from Products.CPSCourrier.tests.layer import IntegrationTestCase
from Products.CPSCourrier.workflows.scripts import reply_to_incoming
from Products.CPSCourrier.relations import make_reply_to
from Products.CPSCourrier.config import RELATION_GRAPH_ID

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
        self.archiver = Archiver(self.portal)
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
            now = {self.archiver.date_field_id: DateTime()}
            for _ in range(2):
                out_mail = reply_to_incoming(in_mail)
                self.outgoing_mails.append(out_mail)
                out_mail.getEditableContent().edit(now, out_mail)

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
        #import pdb; pdb.set_trace()
        threads = list(self.archiver.getThreadsToArchive())
        self.assertEquals(len(threads), 1)
        self.assertEquals(len(threads[0]), 6)





def test_suite():
    return unittest.makeSuite(ArchiverIntegrationTestCase)
