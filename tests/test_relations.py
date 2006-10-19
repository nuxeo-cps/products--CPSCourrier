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
from Products.CMFCore.utils import getToolByName
from Products.CPSRelation.node import VersionHistoryResource
from Products.CPSCourrier.tests.layer import IntegrationTestCase

# import things to test
from Products.CPSCourrier.relations import (
    get_thread_for,
    make_reply_to,
    _get_graph,
    _find_root,
    _accumulate_proxy_info,
)
from Products.CPSCourrier.workflows.scripts import reply_to_incoming


class RelationsIntegrationTestCase(IntegrationTestCase):

    def _build_some_thread(self):
        in_mail1 = self.in_mail1
        in_mail2 = self.in_mail2
        wtool = getToolByName(self.portal, 'portal_workflow')
        wtool.doActionFor(in_mail1, 'handle')
        wtool.doActionFor(in_mail2, 'handle')
        self.out_mail11 = reply_to_incoming(in_mail1)
        self.out_mail12 = reply_to_incoming(in_mail1)
        # manually add in_mail2 as reply of out_mail11 (this is the job of the
        # injector that is not yet part of CPSCourrier)
        make_reply_to(in_mail2, self.out_mail11)

        self.out_mail21 = reply_to_incoming(in_mail2)

        # what is the relational structure we do expect
        proxy_structure = (
            (0, self.in_mail1),
            (1, self.out_mail11),
            (2, self.in_mail2),
            (3, self.out_mail21),
            (1, self.out_mail12),
        )
        self.expected_infos = []
        ptool = getToolByName(self.portal, 'portal_proxies')
        for d, px in proxy_structure:
            (info,) = ptool.getProxyInfosFromDocid(
                px.getDocid(), workflow_vars=('review_state',))
            info['from'] = px.getContent().mail_from
            self.expected_infos.append((d, info))

    def test_find_root(self):
        self._build_some_thread()
        g = _get_graph(self.portal)
        docids = [px.getDocid() for px in (self.in_mail1,
                                           self.in_mail2,
                                           self.out_mail11,
                                           self.out_mail12,
                                           self.out_mail21
                                          )]
        for docid in docids:
            node = VersionHistoryResource(docid)
            root_docid = _find_root(g, node).docid
            self.assertEquals(root_docid, docids[0])

    def test_accumulate_proxy_info(self):
        self._build_some_thread()
        ptool = getToolByName(self.portal, 'portal_proxies')
        g = _get_graph(self.portal)
        docids = [px.getDocid() for px in (self.in_mail1,
                                           self.in_mail2,
                                           self.out_mail11,
                                           self.out_mail21,
                                           self.out_mail12,
                                          )]
        nodes = [VersionHistoryResource(docid) for docid in docids]
        # from the top of the tree
        res = _accumulate_proxy_info(g, nodes[0], ptool, depth=0)
        expected = self.expected_infos
        self.assertEquals(res, expected)

        # leafs
        res = _accumulate_proxy_info(g, nodes[3], ptool, depth=3)
        expected = [self.expected_infos[3]]
        self.assertEquals(res, expected)

        res = _accumulate_proxy_info(g, nodes[4], ptool, depth=1)
        expected = [self.expected_infos[4]]
        self.assertEquals(res, expected)

    def test_get_thread_for(self):
        self._build_some_thread()
        expected = self.expected_infos
        for px in (self.in_mail1, self.in_mail2, self.out_mail11,
                   self.out_mail12, self.out_mail21):
            res = get_thread_for(px)
            self.assertEquals(res, expected)



def test_suite():
    return unittest.makeSuite(RelationsIntegrationTestCase)
