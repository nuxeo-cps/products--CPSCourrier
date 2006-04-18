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

from Products.CMFCore.utils import getToolByName, _checkPermission
from Products.CMFCore.permissions import ModifyPortalContent
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

    def test_outgoing_checkouting_from_scratch(self):
        # test the outgoing collaborative editing worklow on a document that
        # is not a reply
        wf = self.wftool['outgoing_mail_wf']
        mtool = getToolByName(self.portal, 'portal_membership')
        checkPerm = mtool.checkPermission

        # member1 creates an outgoing document
        self.flogin('member1', self.mb)
        self.createOutgoing(self.mb, mail_id="outgoing_of_member1")
        proxy = self.mb.outgoing_of_member1
        stack = self.wftool.getStackFor(proxy, 'Pilots')
        stack_mod = proxy.cpscourrier_stack_modify

        # initialy, the proxy is in state "work" with an empty stack
        self.assertEquals(self._get_state(proxy), 'work')
        self.assertEquals(stack.getAllLevels(), [])

        # the stack is empty: only the manager / wsmanager should be able to
        # play with the stack and the owner as well
        self.flogin('reader', self.mb)
        self.failIf(wf.isActionSupported(proxy, 'manage_delegatees'))
        self.login('manager')
        self.assert_(wf.isActionSupported(proxy, 'manage_delegatees'))
        self.flogin('wsmanager', self.mb)
        self.assert_(wf.isActionSupported(proxy, 'manage_delegatees'))
        self.flogin('member2', self.mb)
        self.failIf(wf.isActionSupported(proxy, 'manage_delegatees'))
        self.flogin('member1', self.mb)
        self.assert_(wf.isActionSupported(proxy, 'manage_delegatees'))

        # with an empty stack, only the manager and the wsmanager can modify the
        # document
        self.flogin('reader', self.mb)
        self.failIf(checkPerm('Modify portal content', proxy))
        self.login('manager')
        self.assert_(checkPerm('Modify portal content', proxy))
        self.flogin('wsmanager', self.mb)
        self.assert_(checkPerm('Modify portal content', proxy))
        self.flogin('member2', self.mb)
        self.failIf(checkPerm('Modify portal content', proxy))
        self.flogin('member1', self.mb)
        self.failIf(checkPerm('Modify portal content', proxy))

        # only the manager / wsmanager can create a draft
        self.flogin('reader', self.mb)
        self.failIf(wf.isActionSupported(proxy, 'checkout_draft'))
        self.login('manager')
        self.assert_(wf.isActionSupported(proxy, 'checkout_draft'))
        self.flogin('wsmanager', self.mb)
        self.assert_(wf.isActionSupported(proxy, 'checkout_draft'))
        self.flogin('member2', self.mb)
        self.failIf(wf.isActionSupported(proxy, 'checkout_draft'))
        self.flogin('member1', self.mb)
        self.failIf(wf.isActionSupported(proxy, 'checkout_draft'))

        # member1 takes the lead
        kw = {'current_var_id': 'Pilots',
              'directive': 'response',
              'level': '0',
              'workflow_action_form': 'cpscourrier_roadmap',
              'submit_add': 'Valider',
              'push_ids': ['courrier_user:member1_ftest-mailbox']}
        stack_mod(**kw)
        self.assertEquals(self._get_state(proxy), 'work')
        self.assertEquals(stack.getAllLevels(), [0])
        elt = stack._getLevelContentValues()[0]
        self.assertEquals(elt.getId(), 'courrier_user:member1_ftest-mailbox')

        # she can now modify the document
        self.flogin('reader', self.mb)
        self.failIf(checkPerm('Modify portal content', proxy))
        self.login('manager')
        self.assert_(checkPerm('Modify portal content', proxy))
        self.flogin('wsmanager', self.mb)
        self.assert_(checkPerm('Modify portal content', proxy))
        self.flogin('member2', self.mb)
        self.failIf(checkPerm('Modify portal content', proxy))
        self.flogin('member1', self.mb)
        self.assert_(checkPerm('Modify portal content', proxy))

        # and she can checkout a draft as well
        self.flogin('reader', self.mb)
        self.failIf(wf.isActionSupported(proxy, 'checkout_draft'))
        self.login('manager')
        self.assert_(wf.isActionSupported(proxy, 'checkout_draft'))
        self.flogin('wsmanager', self.mb)
        self.assert_(wf.isActionSupported(proxy, 'checkout_draft'))
        self.flogin('member2', self.mb)
        self.failIf(wf.isActionSupported(proxy, 'checkout_draft'))
        self.flogin('member1', self.mb)
        self.assert_(wf.isActionSupported(proxy, 'checkout_draft'))

        # before going further, member1 adds member2 to the stacks as well at
        # the same level
        kw = {'current_var_id': 'Pilots',
              'directive': 'response',
              'level': '0',
              'workflow_action_form': 'cpscourrier_roadmap',
              'submit_add': 'Valider',
              'push_ids': ['courrier_user:member2_ftest-mailbox']}
        stack_mod(**kw)
        stack = self.wftool.getStackFor(proxy, 'Pilots') # necessary
        self.assertEquals(self._get_state(proxy), 'work')
        self.assertEquals(stack.getAllLevels(), [0])
        elt = stack._getLevelContentValues()[1]
        self.assertEquals(elt.getId(), 'courrier_user:member2_ftest-mailbox')

        # and she can checkout a draft as well
        self.flogin('reader', self.mb)
        self.failIf(wf.isActionSupported(proxy, 'checkout_draft'))
        self.login('manager')
        self.assert_(wf.isActionSupported(proxy, 'checkout_draft'))
        self.flogin('wsmanager', self.mb)
        self.assert_(wf.isActionSupported(proxy, 'checkout_draft'))
        self.flogin('member2', self.mb)
        self.assert_(wf.isActionSupported(proxy, 'checkout_draft'))
        self.flogin('member1', self.mb)
        self.assert_(wf.isActionSupported(proxy, 'checkout_draft'))

        # but member1 is faster and does it first
        self.wftool.doActionFor(proxy, 'checkout_draft', dest_container=self.mb,
                                initial_transition='checkout_draft_in')
        draft = self.mb[proxy.getId()+'_1']

        # the original proxy is completely locked:
        self.assertEquals(self._get_state(proxy), 'locked')
        self.flogin('reader', self.mb)
        self.failIf(checkPerm('Modify portal content', proxy))
        self.login('manager')
        self.failIf(checkPerm('Modify portal content', proxy))
        self.flogin('wsmanager', self.mb)
        self.failIf(checkPerm('Modify portal content', proxy))
        self.flogin('member2', self.mb)
        self.failIf(checkPerm('Modify portal content', proxy))
        self.flogin('member1', self.mb)
        self.failIf(checkPerm('Modify portal content', proxy))

        # its stack is no longer editable by anybody while locked
        self.flogin('reader', self.mb)
        self.failIf(wf.isActionSupported(proxy, 'manage_delegatees'))
        self.login('manager')
        self.failIf(wf.isActionSupported(proxy, 'manage_delegatees'))
        self.flogin('wsmanager', self.mb)
        self.failIf(wf.isActionSupported(proxy, 'manage_delegatees'))
        self.flogin('member2', self.mb)
        self.failIf(wf.isActionSupported(proxy, 'manage_delegatees'))
        self.flogin('member1', self.mb)
        self.failIf(wf.isActionSupported(proxy, 'manage_delegatees'))

        # the draft can only get edited by member1 (and the managers)
        self.assertEquals(self._get_state(draft), 'draft')
        self.flogin('reader', self.mb)
        self.failIf(checkPerm('Modify portal content', draft))
        self.login('manager')
        self.assert_(checkPerm('Modify portal content', draft))
        self.flogin('wsmanager', self.mb)
        self.assert_(checkPerm('Modify portal content', draft))
        self.flogin('member2', self.mb)
        self.failIf(checkPerm('Modify portal content', draft))
        self.flogin('member1', self.mb)
        self.assert_(checkPerm('Modify portal content', draft))

        # so he does it by changing the title
        draft_doc = draft.getEditableContent()
        draft_doc.edit(Title='A better title', proxy=draft)

        # only member1 (the owner of the draft) and the managers can accept the
        # modification
        self.flogin('reader', self.mb)
        self.failIf(wf.isActionSupported(draft, 'checkin_draft'))
        self.login('manager')
        self.assert_(wf.isActionSupported(draft, 'checkin_draft'))
        self.flogin('wsmanager', self.mb)
        self.assert_(wf.isActionSupported(draft, 'checkin_draft'))
        self.flogin('member2', self.mb)
        self.failIf(wf.isActionSupported(draft, 'checkin_draft'))
        self.flogin('member1', self.mb)
        self.assert_(wf.isActionSupported(draft, 'checkin_draft'))

        # and so he does
        self.wftool.doActionFor(draft, 'checkin_draft',
                                dest_container=self.mb,
                                dest_objects=[proxy],
                                checkin_transition="unlock")

        # the change is the title has been merged
        self.assertEquals(proxy.Title(), 'A better title')

        # the stack has not been affected by the operation
        stack = self.wftool.getStackFor(proxy, 'Pilots') # necessary
        self.assertEquals(self._get_state(proxy), 'work')
        self.assertEquals(stack.getAllLevels(), [0])
        elts = stack._getLevelContentValues()
        self.assertEquals([e.getId() for e in elts],
                          ['courrier_user:member1_ftest-mailbox',
                           'courrier_user:member2_ftest-mailbox'])

        # cleaning the proxy not to pollute other tests
        self.mb.manage_delObjects([proxy.getId()])

    def test_outgoing_validating_from_scratch(self):
        # test the outgoing validation worklow on a document that is not a reply
        wf = self.wftool['outgoing_mail_wf']
        mtool = getToolByName(self.portal, 'portal_membership')
        checkPerm = mtool.checkPermission

        # member1 creates an outgoing document
        self.flogin('member1', self.mb)
        self.createOutgoing(self.mb, mail_id="outgoing_of_member1")
        proxy = self.mb.outgoing_of_member1
        stack = self.wftool.getStackFor(proxy, 'Pilots')
        stack_mod = proxy.cpscourrier_stack_modify

        # initialy, the proxy is in state "work" with an empty stack
        self.assertEquals(self._get_state(proxy), 'work')
        self.assertEquals(stack.getAllLevels(), [])

        # member1 takes the lead
        kw = {'current_var_id': 'Pilots',
              'directive': 'response',
              'level': '0',
              'workflow_action_form': 'cpscourrier_roadmap',
              'submit_add': 'Valider',
              'push_ids': ['courrier_user:member1_ftest-mailbox']}
        stack_mod(**kw)
        self.assertEquals(self._get_state(proxy), 'work')
        self.assertEquals(stack.getAllLevels(), [0])
        elt = stack._getLevelContentValues()[0]
        self.assertEquals(elt.getId(), 'courrier_user:member1_ftest-mailbox')

        # member1 (the Pilot) and the managers can delete the mail
        self.flogin('reader', self.mb)
        self.failIf(wf.isActionSupported(proxy, 'delete'))
        self.login('manager')
        self.assert_(wf.isActionSupported(proxy, 'delete'))
        self.flogin('wsmanager', self.mb)
        self.assert_(wf.isActionSupported(proxy, 'delete'))
        self.flogin('member2', self.mb)
        self.failIf(wf.isActionSupported(proxy, 'delete'))
        self.flogin('member1', self.mb)
        self.assert_(wf.isActionSupported(proxy, 'delete'))

        # member1 (the Pilot) and the managers can then triggers the validate
        # transition
        self.flogin('reader', self.mb)
        self.failIf(wf.isActionSupported(proxy, 'validate'))
        self.login('manager')
        self.assert_(wf.isActionSupported(proxy, 'validate'))
        self.flogin('wsmanager', self.mb)
        self.assert_(wf.isActionSupported(proxy, 'validate'))
        self.flogin('member2', self.mb)
        self.failIf(wf.isActionSupported(proxy, 'validate'))
        self.flogin('member1', self.mb)
        self.assert_(wf.isActionSupported(proxy, 'validate'))

        # and then she does
        self.wftool.doActionFor(proxy, 'validate')
        self.assertEquals(self._get_state(proxy), 'validated')

        # member1 (the Pilot) and the managers can then triggers the invalidate
        # transition
        self.flogin('reader', self.mb)
        self.failIf(wf.isActionSupported(proxy, 'invalidate'))
        self.login('manager')
        self.assert_(wf.isActionSupported(proxy, 'invalidate'))
        self.flogin('wsmanager', self.mb)
        self.assert_(wf.isActionSupported(proxy, 'invalidate'))
        self.flogin('member2', self.mb)
        self.failIf(wf.isActionSupported(proxy, 'invalidate'))
        self.flogin('member1', self.mb)
        self.assert_(wf.isActionSupported(proxy, 'invalidate'))


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

        # now test that member1 of **mailbox 2** can reuse the answer
        # XXX this should go in a separate testcase, nothing to do with stacks

        utool = getToolByName(self.portal, 'portal_url')
        self.flogin('member1', self.mb2)
        # here's the point of the test
        self.failIf(_checkPermission(ModifyPortalContent, self.mb))

        self.wftool.invokeFactoryFor(self.mb2, 'Incoming Mail', 'other')
        self.wftool.doActionFor(self.mb2.other, 'handle')
        self.wftool.doActionFor(self.mb2.other, 'answer',
                                base_reply_rpath=utool.getRpath(outgoing))
        # counter was incremented
        self.assertEquals(outgoing.getContent().template_usage, 1)

        # cleanings
        self.mb.manage_delObjects(['re'])
        self.mb2.manage_delObjects(['other'])

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(CourrierOutgoingStackFunctionalTestCase),
        unittest.makeSuite(CourrierIncomingStackFunctionalTestCase),
        doctest.DocTestSuite('Products.CPSCourrier.workflows.stacks'),
        doctest.DocFileTest(
            'doc/developer/stacks.txt',
            package='Products.CPSCourrier',
            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS),
        ))
