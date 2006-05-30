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
# $Id$
"""XML export of old threads of mail

This archiver assumes the catalog supports batching (ie is a lucene catalog).
"""

import logging
import os
from DateTime import DateTime

from zope.app import zapi
from zope.component import adapts
from zope.interface import implements

from Acquisition import aq_base, aq_inner, aq_parent
from ZODB.loglevels import BLATHER as VERBOSE
from zExceptions import NotFound
from Products.CMFCore.utils import getToolByName
from Products.CPSCourrier.config import ARCHIVE_MIN_AGE, ARCHIVE_HOME
from Products.CPSCourrier.relations import get_thread_for
from Products.CPSDocument.exportimport import getCPSObjectValues
from Products.GenericSetup.context import DirectoryExportContext
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import ISetupEnviron

from Products.CPSCore.interfaces import ICPSProxy

logger = logging.getLogger('CPSCourrier.archive')

class CPSProxyXMLAdapter(XMLAdapterBase):
    """XML (import and) exporter for a CPSProxy

    Store the Proxy data (docid, WF history, ...) and the document data in the
    same XML file (+ subfiles).

    This also export the IS_REPLY_TO information.
    """

    adapts(ICPSProxy, ISetupEnviron)
    implements(IBody)

    _LOGGER_ID = 'cpsproxy'

    def _getObjectNode(self, name, i18n=True):
        node = XMLAdapterBase._getObjectNode(self, name, i18n)
        node.setAttribute('portal_type', self.context.getPortalTypeName())
        return node

    def _exportNode(self):
        """Export the object as a DOM node"""
        node = self._getObjectNode('object')
        ob = self.context
        exporter = zapi.queryMultiAdapter((ob.getContent(), self.environ), IBody)
        node.appendChild(self._extractDocid())
        node.appendChild(self._extractWorkflowHistory())
        node.appendChild(self._extractRelation())
        node.appendChild(exporter._extractObjects())
        node.appendChild(exporter._extractDocumentFields())
        msg = "Proxy %r exported." % self.context.getId()
        self._logger.log(VERBOSE, msg)
        return node

    def _extractDocid(self):
        fragment = self._doc.createDocumentFragment()
        return fragment

    def _extractWorkflowHistory(self):
        fragment = self._doc.createDocumentFragment()
        return fragment

    def _extractRelation(self):
        fragment = self._doc.createDocumentFragment()
        return fragment


def exportCPSObjectsWithDoc(obj, parent_path, context):
    """Export CPS proxies and related documents subfields.

    Recursion also happens for specific CPS subobjects.

    Also use the 'subdir' kw of context.writeDataFile to play nicely with 
    DirectoryExportContext.
    """
    exporter = zapi.queryMultiAdapter((obj, context), IBody)
    id = obj.getId().replace(' ', '_')
    if exporter:
        if exporter.name:
            id = '%s%s' % (id, exporter.name)
        filename = '%s%s' % (id, exporter.suffix)
        body = exporter.body
        if body is not None:
            context.writeDataFile(filename, body, exporter.mime_type,
                                  subdir=parent_path)

    sub_path = "%s%s/" % (parent_path, id)
    # subojects (contained documents or flexible schemas and layouts)
    if getattr(aq_base(obj), 'objectValues', None) is not None:
        for sub in getCPSObjectValues(obj):
            exportCPSObjectsWithDoc(sub, sub_path, context)

    # field subobjects of the related document if any
    if getattr(aq_base(obj), 'getContent', None) is not None:
        doc = obj.getContent()
        for sub in getCPSObjectValues(doc):
            exportCPSObjectsWithDoc(sub, sub_path, context)




class Archiver:

    # review states of proxies to be archived
    review_states = ['closed', 'trash', 'sent']

    # portal types of proxies to be archived
    portal_types = ['Incoming Mail', 'Outgoing Mail']

    # date attribute used to discriminate
    date_field_id = 'ModificationDate'

    def __init__(self, portal, archive_home=ARCHIVE_HOME):
        self._portal = portal
        setup_tool = getToolByName(portal, "portal_setup")
        if not os.path.exists(archive_home):
            os.mkdirs(archive_home)
        if not os.path.isdir(archive_home):
            raise IOError("%s is not a directory" % archive_home)
        self._context = DirectoryExportContext(setup_tool, archive_home)

    def getThreadsToArchive(self):
        """Generate lists of proxies that are to be archived

        A proxy is to be archived if the whole thread of related mails are
        either in state closed, trash or sent and older that ARCHIVE_MIN_AGE.

        Candidate proxies are found thanks to a catalog search.
        """

        # set of a allowed states to speed up membership tests
        review_states = set(self.review_states)

        # maximum creation date
        date_max = DateTime() - ARCHIVE_MIN_AGE

        # find candidate proxies for archiving
        query = {
            'portal_type': self.portal_types,
            'review_state': self.review_states,
            self.date_field_id: {
                'query': date_max,
                'range': 'max',
            },
            # process 100 proxies at a time: trade off between number of brains
            # loaded in memory and number of requests to the catalog
            'b_size': 100,
            'b_start': 0,
        }
        catalog = getToolByName(self._portal, 'portal_catalog')
        brains = catalog(**query)

        while brains:

            # record the set of rpath of proxies that where already processed to
            # avoid duplication
            rpaths_done = set()

            for brain in brains:
                if brain['relative_path'] in rpaths_done:
                    # already seen in a thread
                    continue

                try:
                    thread_seed = brain.getObject()
                except NotFound:
                    thread_seed = None
                if thread_seed is None:
                    # the proxy has been deleted since last catalog query
                    continue

                thread_info = get_thread_for(thread_seed)
                proxies = []
                invalid_thread = False

                for _, proxy_info in thread_info:
                    rpaths_done.add(proxy_info['rpath'])
                    proxy = proxy_info['object']
                    if proxy_info['review_state'] not in review_states:
                        invalid_thread = True
                        logger.debug('Proxy with info %s has wrong review state',
                                     proxy_info)
                        break
                    dm = proxy.getContent().getDataModel()
                    proxy_date = dm[self.date_field_id]
                    if  proxy_date > date_max:
                        invalid_thread = True
                        logger.debug('Proxy with info %s is not old enough: '
                                     '%s > %s', proxy_info, proxy_date, date_max)
                        break
                    proxies.append(proxy)

                if not invalid_thread:
                    logger.debug('Next thread to archive: %s' % proxies)
                    yield proxies

            query['b_start'] = query['b_start'] + query['b_size']
            brains = catalog(**query)

    def exportProxyToXml(self, proxy):
        """Export a proxy to the XML profile directory"""
        utool = getToolByName(self._portal, 'portal_url')
        path = utool.getRpath(proxy)
        parent_path, _ = path.rsplit('/', 1)
        exportCPSObjectsWithDoc(proxy, parent_path + '/', self._context)

    def archive(self):
        """Export and delete thread of old proxies"""
        evtool = getToolByName(self._portal, 'portal_eventservice')
        archived_mails = 0
        for thread in self.getThreadsToArchive():
            for proxy in thread:
                # exporting the whole thread
                self.exportProxyToXml(proxy)
            for proxy in thread:
                # deleting the whole thread
                mb = aq_parent(aq_inner(proxy))
                evtool.notifyEvent('workflow_delete', proxy, {})
                mb.manage_delObjects([proxy.getId()])
            archived_mails += len(thread)
        return archived_mails



