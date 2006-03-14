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
from zope.testing import doctest


from Products.CMFCore.utils import getToolByName

from Products.CPSDefault.tests.CPSTestCase import CPSTestCase
from Products.CPSCourrier.tests.layer import CPSCourrierLayer

# import things to test
from Products.CPSCourrier.workflows.scripts import (
    reply_to_incoming, flag_incoming_answered, flag_incoming_handled)
from Products.CPSCourrier.config import RELATION_GRAPH_ID


class WorkflowScriptsIntegrationTestCase(CPSTestCase):
    layer = CPSCourrierLayer
    MBG_ID = 'test_mailbox_group'
    MB_ID = 'test_mailbox'

    def afterSetUp(self):
        self.login('manager')
        # create test sandboxes in the mailboxes space
        wftool = getToolByName(self.portal, 'portal_workflow')
        ttool = getToolByName(self.portal, 'portal_types')
        mailboxes = self.portal.mailboxes

        wftool.invokeFactoryFor(mailboxes, 'Mailbox Group', self.MBG_ID)
        self.mbg = mailboxes[self.MBG_ID]

        wftool.invokeFactoryFor(self.mbg, 'Mailbox', self.MB_ID,
                                **{'from': 'test_mailbox@cpscourrier.com'})
        self.mb = self.mbg[self.MB_ID]

        # add some incoming mails
        incoming_mail_data = {
            'in_mail1': {
                'Title': 'Test mail 1',
                'to': ['foo@foo.com'],
                'from': 'bar@foo.com',
            },
            'in_mail2': {
                'Title': 'Re: Test mail 1',
                'to': ['bar2@foo.com', 'toto@email.com'],
                'from': 'foo@foo.com',
            },
        }
        mail_fti = ttool['Incoming Mail']
        for mail_id, mail_data in incoming_mail_data.items():
            dm = mail_fti.getDataModel(None)
            wftool.invokeFactoryFor(self.mb, 'Incoming Mail', mail_id,
                                    datamodel=dm, **mail_data)
            setattr(self, mail_id, self.mb[mail_id])

    def afterTearDown(self):
        # delete the test areas
        self.portal.mailboxes.manage_delObjects([self.MBG_ID])
        self.logout()

    # make tests less verbose by using custom accessor for WF state
    def _get_state(self, ob):
        return ob.workflow_history.values()[0][-1]['review_state']

    def _set_state(self, ob, state):
        ob.workflow_history.values()[0][-1]['review_state'] = state

    def test_reply_to_incoming(self):
        rtool = getToolByName(self.portal, 'portal_relations')

        # add 'Re:' to the incoming mail title
        out_mail1 = reply_to_incoming(self.in_mail1)
        self.assertEquals(out_mail1.Title(), 'Re: Test mail 1')
        doc1 = out_mail1.getContent()
        self.assertEquals(doc1['from'], 'test_mailbox@cpscourrier.com')
        self.assertEquals(doc1['to'], ['bar@foo.com'])

        # check that they are related
        res = rtool.getRelationsFor(RELATION_GRAPH_ID,
                                int(out_mail1.getDocid()),
                                'is_reply_to')
        expected = (int(self.in_mail1.getDocid()),)
        self.assertEquals(expected, res)

        # do not add the 'Re:' prefix twice
        out_mail2 = reply_to_incoming(self.in_mail2)
        doc2 = out_mail2.getContent()
        self.assertEquals(out_mail2.Title(), 'Re: Test mail 1')
        self.assertEquals(doc2['from'], 'test_mailbox@cpscourrier.com')
        self.assertEquals(doc2['to'], ['foo@foo.com'])

        # check that they are related
        res = rtool.getRelationsFor(RELATION_GRAPH_ID,
                                int(out_mail2.getDocid()),
                                'is_reply_to')
        expected = (int(self.in_mail2.getDocid()),)
        self.assertEquals(expected, res)

    def test_flag_incoming_answered_1(self):
        # the replying scenario with only one reply to in_mail1
        in_mail1 = self.in_mail1
        out_mail1 = reply_to_incoming(in_mail1)

        # initial states after creation
        self.assertEquals(self._get_state(in_mail1), 'received')
        self.assertEquals(self._get_state(out_mail1), 'work')

        # if incoming mail and outgoing mail are not is states 'answering' and
        # 'sent' respectively, this should not change anything
        flag_incoming_answered(out_mail1)
        self.assertEquals(self._get_state(in_mail1), 'received')
        self.assertEquals(self._get_state(out_mail1), 'work')

        # only incoming mail is in state 'answering' -> nothing either
        self._set_state(in_mail1, 'answering')
        flag_incoming_answered(out_mail1)
        self.assertEquals(self._get_state(in_mail1), 'answering')
        self.assertEquals(self._get_state(out_mail1), 'work')

        # only outgoing mail is in state 'sent' -> nothing either
        self._set_state(in_mail1, 'received')
        self._set_state(out_mail1, 'sent')
        flag_incoming_answered(out_mail1)
        self.assertEquals(self._get_state(in_mail1), 'received')
        self.assertEquals(self._get_state(out_mail1), 'sent')

        # if both incoming and outgoing are on the right state, the transition
        # is triggered
        self._set_state(in_mail1, 'answering')
        flag_incoming_answered(out_mail1)
        self.assertEquals(self._get_state(in_mail1), 'answered')
        self.assertEquals(self._get_state(out_mail1), 'sent')

    def test_flag_incoming_answered_2(self):
        # the replying scenario with several (2) replies to an incoming mail
        in_mail1 = self.in_mail1
        out_mail1 = reply_to_incoming(in_mail1)
        out_mail2 = reply_to_incoming(in_mail1)

        # initial states after creation
        self.assertEquals(self._get_state(in_mail1), 'received')
        self.assertEquals(self._get_state(out_mail1), 'work')
        self.assertEquals(self._get_state(out_mail2), 'work')

        # if incoming mail and outgoing mails are not is states 'answering' and
        # 'sent' respectively, this should not change anything
        flag_incoming_answered(out_mail1)
        self.assertEquals(self._get_state(in_mail1), 'received')
        self.assertEquals(self._get_state(out_mail1), 'work')
        self.assertEquals(self._get_state(out_mail2), 'work')

        # only incoming mail is in state 'answering' -> nothing either
        self._set_state(in_mail1, 'answering')
        flag_incoming_answered(out_mail1)
        self.assertEquals(self._get_state(in_mail1), 'answering')
        self.assertEquals(self._get_state(out_mail1), 'work')
        self.assertEquals(self._get_state(out_mail2), 'work')

        # only outgoing mails are in state 'sent' -> nothing either
        self._set_state(in_mail1, 'received')
        self._set_state(out_mail1, 'sent')
        self._set_state(out_mail2, 'sent')
        flag_incoming_answered(out_mail1)
        self.assertEquals(self._get_state(in_mail1), 'received')
        self.assertEquals(self._get_state(out_mail1), 'sent')
        self.assertEquals(self._get_state(out_mail2), 'sent')

        # if only one of the replies is 'sent' -> nothing either
        self._set_state(in_mail1, 'answering')
        self._set_state(out_mail1, 'sent')
        self._set_state(out_mail2, 'work')
        flag_incoming_answered(out_mail1)
        self.assertEquals(self._get_state(in_mail1), 'answering')
        self.assertEquals(self._get_state(out_mail1), 'sent')
        self.assertEquals(self._get_state(out_mail2), 'work')

        # if both incoming and outgoing are on the right state, the transition
        # is triggered
        self._set_state(out_mail2, 'sent')
        flag_incoming_answered(out_mail1)
        self.assertEquals(self._get_state(in_mail1), 'answered')
        self.assertEquals(self._get_state(out_mail1), 'sent')
        self.assertEquals(self._get_state(out_mail2), 'sent')

    def test_flag_incoming_handled(self):
        in_mail1 = self.in_mail1
        out_mail1 = reply_to_incoming(in_mail1)
        out_mail2 = reply_to_incoming(in_mail1)
        out_mail3 = reply_to_incoming(in_mail1)
        self._set_state(in_mail1, 'answering')

        # flag_incoming_answered must change the in_mail1 state only if there is
        # only one reply remaining
        flag_incoming_answered(out_mail1)
        self.assertEquals(self._get_state(in_mail1), 'answering')

        # unlink outmail2, and retry
        rtool = getToolByName(in_mail1, 'portal_relations')
        rtool.deleteRelationFor(RELATION_GRAPH_ID,
                                int(out_mail2.getDocid()),
                                'is_reply_to',
                                int(in_mail1.getDocid()))
        flag_incoming_answered(out_mail1)
        self.assertEquals(self._get_state(in_mail1), 'answering')

        # unlink outmail3, and retry
        rtool = getToolByName(in_mail1, 'portal_relations')
        rtool.deleteRelationFor(RELATION_GRAPH_ID,
                                int(out_mail3.getDocid()),
                                'is_reply_to',
                                int(in_mail1.getDocid()))
        linked_replies = rtool.getRelationsFor(RELATION_GRAPH_ID,
                                int(in_mail1.getDocid()),
                                'has_reply')
        # out_mail1 is the last reply: the transition on in_mail1 is triggered
        self.assertEquals(linked_replies, (int(out_mail1.getDocid()),))
        flag_incoming_handled(out_mail1)
        self.assertEquals(self._get_state(in_mail1), 'handled')







def test_suite():
    return unittest.makeSuite(WorkflowScriptsIntegrationTestCase)
