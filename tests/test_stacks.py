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

        # manager still can manage the stack (see later)
        self.login('manager')
        wf = self.wftool['incoming_mail_wf']
        #self.assert_(wf.isActionSupported(self.incoming, 'manage_delegatees'))
        self.flogin('member1', self.mb)

        # member1 adds member2 below himself
        kws = {'current_var_id': 'Pilots',
               'directive': 'response',
               'level': '-1',
               'workflow_action_form': 'cpscourrier_roadmap',
               'submit_add': 'Valider',
               'push_ids': ['courrier_user:member2']}
        stack_mod(**kws)
        self.assertEquals(stack.getAllLevels(), [-1, 0])

        # member1 adds member2 between member1 and member2
        kws = {'current_var_id': 'Pilots',
               'directive': 'response',
               'level': '-1_0',
               'workflow_action_form': 'cpscourrier_roadmap',
               'submit_add': 'Valider',
               'push_ids': ['courrier_user:member2']}
        stack_mod(**kws)
        stack = self.wftool.getStackFor(self.incoming, 'Pilots') # necessary
        self.assertEquals(stack.getAllLevels(), [-2, -1, 0])

        # check what will be displayed
        for_render = stack.getStackContentForRender(self.incoming)
        self.assertEquals(for_render[1][0]['items'][0]['identite'],
                          'member1_ftest-mailbox')

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(CourrierOutgoingStackFunctionalTestCase),
        unittest.makeSuite(CourrierIncomingStackFunctionalTestCase),
        doctest.DocFileTest('doc/developer/stacks.txt',
                            package='Products.CPSCourrier',
                            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS),
        ))
