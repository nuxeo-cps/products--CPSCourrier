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
import transaction

from zope.app import zapi
from zope.component import adapts
from zope.interface import implements

from Acquisition import aq_base, aq_inner, aq_parent
from AccessControl import Unauthorized
from ZODB.loglevels import BLATHER as VERBOSE
from zExceptions import NotFound
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CPSCourrier.config import (
    ARCHIVE_MIN_AGE, ARCHIVE_HOME, HAS_REPLY, RELATION_PREFIX, RELATION_GRAPH_ID)
from Products.CPSCourrier.relations import get_thread_for
from Products.CPSDocument.exportimport import getCPSObjectValues
from Products.GenericSetup.context import DirectoryExportContext
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import ISetupEnviron
from Products.CPSRelation.interfaces import IVersionHistoryResource
from Products.CPSRelation.node import PrefixedResource

from Products.CPSCore.interfaces import ICPSProxy

logger = logging.getLogger('CPSCourrier.archive')

class CPSProxyXMLAdapter(XMLAdapterBase):
    """XML (import and) exporter for a CPSProxy

    Store the Proxy data such as WF history and the document data in the
    same XML file (+ subfiles).

    This also export the HAS_REPLY relation.
    """

    adapts(ICPSProxy, ISetupEnviron)
    implements(IBody)

    _LOGGER_ID = 'cpsproxy'

    _wf_vars_type_map = {
        str: 'str',
        int: 'int',
        float: 'float',
        bool: 'bool',
        type(DateTime()): 'date',
    }

    def _getObjectNode(self, name, i18n=True):
        node = XMLAdapterBase._getObjectNode(self, name, i18n)
        node.setAttribute('portal_type', self.context.getPortalTypeName())
        return node

    def _exportNode(self):
        """Export the object as a DOM node"""
        node = self._getObjectNode('object')
        ob = self.context
        exporter = zapi.queryMultiAdapter((ob.getContent(), self.environ), IBody)
        node.appendChild(self._extractWorkflowHistory())
        node.appendChild(self._extractRelation())
        node.appendChild(exporter._extractObjects())
        node.appendChild(exporter._extractDocumentFields())
        msg = "Proxy %r exported." % self.context.getId()
        self._logger.log(VERBOSE, msg)
        return node

        fragment = self._doc.createDocumentFragment()
        return fragment

    def _extractWorkflowHistory(self):
        fragment = self._doc.createDocumentFragment()
        for wf_id, wf_history in sorted(self.context.workflow_history.items()):
            node = self._doc.createElement('wf_history')
            node.setAttribute('name', wf_id)
            for step in wf_history:
                step_node = self._doc.createElement('step')
                for name, value in sorted(step.items()):
                    type_ = self._wf_vars_type_map.get(type(value))
                    if type_ is None:
                        logger.debug('Could not serialize wf var %s: %s'
                                     'for document %s', name, value, self.context)
                        continue
                    if type_ == 'date':
                        value = value.ISO8601()
                    var_node = self._doc.createElement('variable')
                    var_node.setAttribute('name', name)
                    var_node.setAttribute('type', type_)
                    var_node.appendChild(self._doc.createTextNode(str(value)))
                    step_node.appendChild(var_node)
                node.appendChild(step_node)
            fragment.appendChild(node)
        return fragment

    def _extractRelation(self):
        fragment = self._doc.createDocumentFragment()
        node = self._doc.createElement('relation')
        node.setAttribute('name', "%s:%s" % (RELATION_PREFIX, HAS_REPLY))
        rtool = getToolByName(self.context, 'portal_relations')
        ptool = getToolByName(self.context, 'portal_proxies')
        g = rtool.getGraph(RELATION_GRAPH_ID)
        replies = g.getObjects(IVersionHistoryResource(self.context),
                               PrefixedResource(RELATION_PREFIX, HAS_REPLY))
        for reply in replies:
            infos = ptool.getProxyInfosFromDocid(reply.docid)
            for info in infos:
                child = self._doc.createElement('target')
                child.setAttribute('rpath', info['rpath'])
            node.appendChild(child)
        fragment.appendChild(node)
        return fragment


def exportCPSObjectsWithDoc(obj, parent_path, context):
    """Export CPS proxies and related documents subfields.

    Recursion also happens for specific CPS subobjects.

    Also use the 'subdir' kw of context.writeDataFile to play nicely with
    DirectoryExportContext.
    """
    exporter = zapi.queryMultiAdapter((obj, context), IBody,
                                      'cpscourrier_archive')
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
    """Implement CPSCourrier specific archiving logic

    Old mail documents in specified review states are exported to XML and
    deleted from the ZODB.

    Before archiving, a list of configurable transitions can get
    automatically triggered on old unwanted proxies to clean up the threads
    to archive.

    To maximize efficiency, the repository should be purged and the ZODB packed
    after triggering the archiving machinery (cf cpshousekeeping to automate
    such tasks).

    Use a special XMLAdapter to export the proxy informations using the
    GenericSetup machinery.
    """
    # transitions to trigger before archiving
    auto_transitions = [
        (['Incoming Email', 'Incoming Pmail'], 'pending', 'discard'),
        (['Incoming Email', 'Incoming Pmail'], 'trash', 'delete'),
    ]

    # review states of proxies to be archived
    review_states_to_archive = ['closed', 'sent']

    # portal types of proxies to be archived
    portal_types = ['Incoming Email', 'Outgoing Email',
                    'Incoming Pmail', 'Outgoing Pmail']

    # date attribute used to discriminate
    date_field_id = 'ModificationDate'

    # date index corresponding to the previous field
    date_index_id = "modified"

    def __init__(self, portal, archive_home=ARCHIVE_HOME):
        if not _checkPermission(ManagePortal, portal):
            raise Unauthorized

        self._portal = portal
        setup_tool = getToolByName(portal, "portal_setup")
        if not os.path.exists(archive_home):
            os.makedirs(archive_home)
        if not os.path.isdir(archive_home):
            raise IOError("%s is not a directory" % archive_home)
        self._context = DirectoryExportContext(setup_tool, archive_home)

    def _triggerAutoTransitions(self):
        """Play some transition to cleanup old useless proxies"""

        wftool = getToolByName(self._portal, "portal_workflow")
        date_max = DateTime() - ARCHIVE_MIN_AGE
        count = 0

        for ptypes, review_state, transition in self.auto_transitions:
            query = {
                'portal_type': ptypes,
                'review_state': review_state,
                self.date_index_id: {
                    'query': date_max,
                    'range': 'max',
                },
                # process 100 proxies at a time: trade off between number of
                # brains loaded in memory and number of requests to the
                # catalog
                'b_size': 100,
                'b_start': 0,
            }
            catalog = getToolByName(self._portal, 'portal_catalog')
            brains = catalog(**query)

            while brains:
                for brain in brains:
                    try:
                        proxy = brain.getObject()
                    except NotFound:
                        proxy = None
                    if proxy is None:
                        # the proxy has been deleted since last catalog query
                        continue
                    try:
                        logger.info('triggering %s on %r', transition, proxy)
                        wftool.doActionFor(proxy, transition)
                        count += 1
                    except WorkflowException:
                        logger.warning("could not execute %s on %r",
                                        transition, proxy)
                        pass


                query['b_start'] = query['b_start'] + query['b_size']
                brains = catalog(**query)

            # necessary to update the catalog because of the transaction
            # manager that pospones catalog reindexation at they end of the
            # transaction
            transaction.commit()
        return count

    def getThreadsToArchive(self):
        """Generate lists of proxies that are to be archived

        A proxy is to be archived if the whole thread of related mails are
        either in state closed, trash or sent and older that ARCHIVE_MIN_AGE.

        Candidate proxies are found thanks to a catalog search.
        """

        # set of a allowed states to speed up membership tests
        review_states = set(self.review_states_to_archive)

        # maximum creation date
        date_max = DateTime() - ARCHIVE_MIN_AGE

        # find candidate proxies for archiving
        query = {
            'portal_type': self.portal_types,
            'review_state': self.review_states_to_archive,
            self.date_index_id: {
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
                        logger.debug('Proxy %s has wrong review state',
                                     proxy_info)
                        break
                    dm = proxy.getContent().getDataModel()
                    proxy_date = dm[self.date_field_id]
                    if  proxy_date > date_max:
                        invalid_thread = True
                        logger.debug('Proxy %s is not old enough: %s > %s',
                                     proxy_info, proxy_date, date_max)
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
        self._triggerAutoTransitions()
        archived_mails = 0
        for thread in self.getThreadsToArchive():
            for proxy in thread:
                # exporting the whole thread
                logger.info("archiving %r", proxy)
                self.exportProxyToXml(proxy)
            for proxy in thread:
                # deleting the whole thread
                mb = aq_parent(aq_inner(proxy))
                evtool.notifyEvent('workflow_delete', proxy, {})
                mb.manage_delObjects([proxy.getId()])
            archived_mails += len(thread)
        return archived_mails

