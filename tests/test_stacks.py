# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
# Author: Georges Racinet <gracinet@nuxeo.com>
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

import unittest
from zope.testing import doctest
from layer import CourrierFunctionalTestCase

from Products.CMFCore.utils import getToolByName
from Products.CPSCourrier.workflows.stacks import CourrierStack
from Products.CPSCourrier.config import (
    RELATION_GRAPH_ID,
    IS_REPLY_TO,
    HAS_REPLY,
    STACK_ID,
    )

class CourrierOutgoingStackFunctionalTestCase(CourrierFunctionalTestCase):
    """ Quasifunctional tests for outgoing mails."""

    def afterSetUp(self):
        CourrierFunctionalTestCase.afterSetUp(self)
        self.stack = CourrierStack()
        self.login('manager')
        self.createOutgoing()

    def beforeTearDown(self):
        self.mb.manage_delObjects([self.outgoing_id])
        self.logout()

    def test_getStackContentForRender(self):
        self.stack.push(push_ids=('example:A', 'example:B'),
                        levels=(0,1,),
                        data_lists=('d1', 'd2'),
                        d1=('A1', 'B1',),
                        d2=('A2', 'B2',))

        extr = self.stack.getStackContentForRender(self.outgoing,
                                                   mode='view')
        # TODO: assertions


class CourrierIncomingStackFunctionalTestCase(CourrierFunctionalTestCase):

    def afterSetUp(self):
        CourrierFunctionalTestCase.afterSetUp(self)
        self.login('manager')
        self.createIncoming()

    def beforeTearDown(self):
        self.mb.manage_delObjects([self.incoming_id])
        self.logout()

    def test_handle_stack_manage(self):
        stack_mod = self.incoming.cpscourrier_stack_modify

        # member1 handles the mail
        self.flogin('member1', self.mb)
        self.wftool.doActionFor(self.incoming, 'handle')

        stack = self.wftool.getStackFor(self.incoming, 'Pilots')
        self.assertEquals(stack.getAllLevels(), [0])
        elt = stack._getLevelContentValues()[0]
        self.assertEquals(elt['directive'], 'handle')

        # Checking perms for other roles
        wf = self.wftool['incoming_mail_wf']

        self.login('manager')
        self.assert_(wf.isActionSupported(self.incoming, 'manage_delegatees'))
        self.flogin('wsmanager', self.mb)
        self.assert_(wf.isActionSupported(self.incoming, 'manage_delegatees'))
        self.flogin('member2', self.mb)
        self.failIf(wf.isActionSupported(self.incoming, 'manage_delegatees'))
        self.flogin('member1', self.mb)

        # member1 adds member2 below himself
        kws = {'current_var_id': 'Pilots',
               'directive': 'response',
               'level': '-1',
               'workflow_action_form': 'cpscourrier_roadmap',
               'submit_add': 'Valider',
               'push_ids': ['courrier_user:member2_ftest-mailbox']}
        stack_mod(**kws)
        self.assertEquals(stack.getAllLevels(), [-1, 0])

        # member1 adds member3 (upper) between member1 and member2
        kws = {'current_var_id': 'Pilots',
               'directive': 'response',
               'level': '-1_0',
               'workflow_action_form': 'cpscourrier_roadmap',
               'submit_add': 'Valider',
               'push_ids': ['courrier_user:member3_ftest-mailbox-group']}
        stack_mod(**kws)
        stack = self.wftool.getStackFor(self.incoming, 'Pilots') # necessary
        self.assertEquals(stack.getAllLevels(), [-2, -1, 0])

        # check what will be displayed
        for_render = stack.getStackContentForRender(self.incoming)
        self.assertEquals(for_render[1][0]['items'][0]['identite'],
                          'member1_ftest-mailbox')

        # member1 delegates member3
        self.wftool.doActionFor(self.incoming, 'move_down_delegatees',
                                current_wf_var_id='Pilots')
        self.failIf(wf.isActionSupported(self.incoming, 'answer'))
        self.flogin('member2', self.mb)
        self.failIf(wf.isActionSupported(self.incoming, 'answer'))
        self.flogin('member3', self.mbg)
        self.assert_(wf.isActionSupported(self.incoming, 'answer'))

    def test_default_roadmap(self):
        stack_mod = self.mb.cpscourrier_stack_modify

        # Test that we don't fail if we try and handle from default roadmap
        # and there isn't any
        self.flogin('member1', self.mb)
        self.wftool.doActionFor(self.incoming, 'handle',
                                use_parent_roadmap=True)
        stack = self.wftool.getStackFor(self.incoming, 'Pilots')
        for_render = stack.getStackContentForRender(self.incoming)
        self.assertEquals(for_render[1][0]['items'][0]['identite'],
                          'member1_ftest-mailbox')
        self.wftool.doActionFor(self.incoming, 'reset')

        # wsmanager of mb logs in and builds the default roadmap:
        # -1:member1, 0:member3
        self.flogin('wsmanager', self.mb)
        kws = {'current_var_id': 'Pilots',
               'directive': 'response',
               'level': '0',
               'workflow_action_form': 'cpscourrier_roadmap',
               'submit_add': 'Valider',
               'push_ids': ['courrier_user:member3_ftest-mailbox-group']}
        stack_mod(**kws)
        kws = {'current_var_id': 'Pilots',
               'directive': 'response',
               'level': '-1',
               'workflow_action_form': 'cpscourrier_roadmap',
               'submit_add': 'Valider',
               'push_ids': ['courrier_user:member1_ftest-mailbox']}
        stack_mod(**kws)

        # we can insert above current level (should go in unit tests)
        stack = self.wftool.getStackFor(self.mb, 'Pilots')
        insert_render = stack.getStackContentForRender(self.mb,
                                                       mode='insert')
        self.assertEquals(insert_render[0], [1, 0, '-1_0', -1, -2])

        # member2 logs in and handles the incoming mail
        self.flogin('member2', self.mb)
        self.wftool.doActionFor(self.incoming, 'handle',
                                use_parent_roadmap=True)

        # assertions on mail's stack
        stack = self.wftool.getStackFor(self.incoming, 'Pilots')

        # stack holds: -1:member1, 0:member3, 1:member2
        self.assertEquals(stack.getAllLevels(), [-1,0,1])
        for_render = stack.getStackContentForRender(self.incoming)
        self.assertEquals(for_render[1][0]['items'][0]['identite'],
                          'member3_ftest-mailbox-group')
        self.assertEquals(for_render[1][1]['items'][0]['identite'],
                          'member2_ftest-mailbox')
        self.assertEquals(for_render[1][-1]['items'][0]['identite'],
                          'member1_ftest-mailbox')

    def test_answer(self):
        stack_mod = self.incoming.cpscourrier_stack_modify

        # member1 handles the mail
        self.flogin('member1', self.mb)
        self.wftool.doActionFor(self.incoming, 'handle')

        # member1 adds member2 below himself
        kws = {'current_var_id': 'Pilots',
               'directive': 'response',
               'level': '-1',
               'workflow_action_form': 'cpscourrier_roadmap',
               'submit_add': 'Valider',
               'push_ids': ['courrier_user:member2_ftest-mailbox']}
        stack_mod(**kws)

        # member1 creates the answer
        self.wftool.doActionFor(self.incoming, 'answer')

        # retrieve the answer
        rtool = getToolByName(self.portal, 'portal_relations')
        outgoing_docids= rtool.getRelationsFor(RELATION_GRAPH_ID,
                                               int(self.incoming.getDocid()),
                                               HAS_REPLY)
        self.assertEquals(len(outgoing_docids), 1)
        docid = str(outgoing_docids[0])
        pxtool = getToolByName(self.portal, 'portal_proxies')
        proxies = pxtool.listProxies(docid=docid)
        self.assertEquals(len(proxies), 1)
        outgoing = self.portal.unrestrictedTraverse(proxies[0][0])

        # stack has been copied and reversed
        stack = self.wftool.getStackFor(outgoing, 'Pilots')
        self.assertEquals(stack.getAllLevels(), [0, 1])
        for_render = stack.getStackContentForRender(outgoing)
        # was previously at level -1
        self.assertEquals(for_render[1][1]['items'][0]['identite'],
                          'member2_ftest-mailbox')

        # cleaning outgoing proxy
        self.mb.manage_delObjects(['re'])

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(CourrierOutgoingStackFunctionalTestCase),
        unittest.makeSuite(CourrierIncomingStackFunctionalTestCase),
        doctest.DocTestSuite('Products.CPSCourrier.workflows.stacks'),
        doctest.DocFileTest('doc/developer/stacks.txt',
                            package='Products.CPSCourrier',
                            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS),
        ))
