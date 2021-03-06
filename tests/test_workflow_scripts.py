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

import datetime
import unittest
import transaction
import re
from StringIO import StringIO

from DateTime import DateTime
from OFS.Image import File
from Products.CMFCore.utils import getToolByName
from Products.CPSUtil.text import get_final_encoding
from Products.CPSCourrier.tests.layer import IntegrationTestCase
from Products.CPSCourrier.tests.layer import PaperIntegrationTestCase

# import things to test
from Products.CPSCourrier.workflows.scripts import (
    bayes_learn_subject,
    bayes_guess_subject,
    reply_to_incoming,
    flag_incoming_answered,
    flag_incoming_handled,
    forward_mail,
    send_reply,
    init_stack_with_user)
from Products.CPSCourrier.relations import (
    unlink,
    get_original_message_docid,
    get_replies_docids,
)

class WorkflowScriptsIntegrationTestCase(IntegrationTestCase):

    def xtest_bayes_learn_and_guess(self):
        doc1 = self.in_mail1.getEditableContent()
        doc2 = self.in_mail2.getEditableContent()

        doc1.edit(proxy=self.in_mail1, **{
            'Subject': ['CPSCourrier', 'CPSBayes', 'mail', 'subject4'],
            'Title': 'This is mail1',
            'content': 'This is a mail talking about the CPSBayes features'
                       'used in CPSCourrier',
            'Language': 'en',
        })
        bayes_learn_subject(self.in_mail1)

        doc2.edit(proxy=self.in_mail2, **{
            'Title': 'This is mail2',
            'content': 'This is a mail talking about things that are very '
                       'very similar to mail1 such as the features of CPSBayes'
                       ' that are leveraged by CPSCourrier',
            'Language': 'en',
        })
        bayes_guess_subject(self.in_mail2)
        subject2 = sorted(self.in_mail2.getContent()['Subject']())
        expected = sorted(['CPSCourrier', 'CPSBayes', 'mail'])
        self.assertEquals(subject2, expected)

        # trying again in french instead of english
        doc1.edit(proxy=self.in_mail1, **{
            'Subject': ['jonquille', 'printemps'],
            'Title': 'Ceci est un courrier en francais',
            'content': 'Oui, c\'est le printemps !',
            'Language': 'fr',
        })
        bayes_learn_subject(self.in_mail1)

        doc2.edit(proxy=self.in_mail2, **{
            'Subject': [],
            'Title': 'Ceci est mail2',
            'content': 'Ce message parle ce concepts proches de ceux de mail1 '
                       'comme par exemple les fonctionnalit\xe9s de CPSBayes '
                       'qui sont mises \xe0 profit dans CPSCourrier',
            'Language': 'fr',
        })
        bayes_guess_subject(self.in_mail2)
        subject2 = self.in_mail2.getContent()['Subject']()
        self.assertEquals(subject2, (),
                          'english mail should not affect french classifier')

# This is currently broken is probably due to a bug in BayesCore
#
#        # once again about the printemps this time
#        doc2.edit(proxy=self.in_mail2, **{
#            'Title': 'Ceci est un courrier en francais',
#            'content': 'Oui, c\'est le printemps !',
#            'Language': 'fr',
#        })
#        bayes_guess_subject(self.in_mail2)
#        subject2 = sorted(self.in_mail2.getContent()['Subject']())
#        expected = sorted(['jonquille', 'printemps'])
#        self.assertEquals(subject2, expected)

    def test_reply_to_incoming(self):
        wtool = getToolByName(self.portal, 'portal_workflow')

        # add 'Re:' to the incoming mail title
        if wtool.getInfoFor(self.in_mail1, 'review_state') == 'received':
            wtool.doActionFor(self.in_mail1, 'handle')
        self.out_mail1 = out_mail1 = reply_to_incoming(self.in_mail1)
        self.assertEquals(out_mail1.Title(), 'Re: Test mail 1')
        self.outgoing_doc1 = doc1 = out_mail1.getContent()

        if doc1.portal_type.endswith('Email'):
            # Mailbox sending address
            self.assertEquals(doc1['mail_from'],
                              'test_mailbox@cpscourrier.com')
        else:
            # Recipient of the incoming mail
            self.assertEquals(doc1['mail_from'], 'foo@foo.com')

        self.assertEquals(doc1['mail_to'], ['bar@foo.com'])

        # check that they are related
        res = get_original_message_docid(out_mail1)
        expected = self.in_mail1.getDocid()
        self.assertEquals(expected, res)

        # do not add the 'Re:' prefix twice
        if wtool.getInfoFor(self.in_mail2, 'review_state') == 'received':
            # Email only
            wtool.doActionFor(self.in_mail2, 'handle')
        out_mail2 = reply_to_incoming(self.in_mail2)
        self.outgoing_doc2 = doc2 = out_mail2.getContent()
        self.assertEquals(out_mail2.Title(), 'Re: Test mail 1')
        if doc1.portal_type.endswith('Email'):
            self.assertEquals(doc2['mail_from'],
                              'test_mailbox@cpscourrier.com')
        else:
            # first in the list. In real life paper use the list would be
            # a singleton
            self.assertEquals(doc2['mail_from'], 'bar2@foo.com')

        self.assertEquals(doc2['mail_to'], ['foo@foo.com'])

        # check that they are related
        res = get_original_message_docid(out_mail2)
        expected = self.in_mail2.getDocid()
        self.assertEquals(expected, res)

    def test_reply_to_incoming_with_template(self):
        wtool = getToolByName(self.portal, 'portal_workflow')
        utool = getToolByName(self.portal, 'portal_url')

        # create a first reply and use it a template for a second reply
        state = wtool.getInfoFor(self.in_mail1, 'review_state')
        if state == 'received': # Email only
            wtool.doActionFor(self.in_mail1, 'handle')
        template = reply_to_incoming(self.in_mail1)
        self.assertEquals(template.Title(), 'Re: Test mail 1')
        self.outgoing_doc1 = doc1 = template.getEditableContent()
        if doc1.portal_type.endswith('Email'):
            self.assertEquals(doc1['mail_from'], 'test_mailbox@cpscourrier.com')
        else:
            self.assertEquals(doc1['mail_from'], 'foo@foo.com')
        self.assertEquals(doc1['mail_to'], ['bar@foo.com'])

        # check that they are related
        res = get_original_message_docid(template)
        expected = self.in_mail1.getDocid()
        self.assertEquals(expected, res)

        # edit the template reply, and attach two files
        doc1.edit(content="This content is part of the template",
                  Subject=("subject1", "subject2",), proxy=template)
        ti = doc1.getTypeInfo()
        ti.flexibleAddWidget(doc1, 'mail_flexible', 'file')
        ti.flexibleAddWidget(doc1, 'mail_flexible', 'file')
        dm = ti.getDataModel(doc1, proxy=template)
        self.assert_('file_f0' in dm) # test the test
        self.assert_('file_1_f0' in dm)
        doc1.edit(file_f0=File('file_f0', 'this_is.test',
                               StringIO('This is a test')),
                  file_1_f0=File('file_1_f0', 'other_file.txt',
                                 StringIO('Other foo file'))
                  )

        # create a second reply using the first reply as template
        template_rpath = utool.getRpath(template)
        second_reply = reply_to_incoming(self.in_mail1,
                                         base_reply_rpath=template_rpath)

        # check fields init
        self.assertEquals(second_reply.Title(), 'Re: Test mail 1')
        self.outgoing_doc2 = doc2 = second_reply.getContent()
        if doc1.portal_type.endswith('Email'):
            self.assertEquals(doc2['mail_from'], 'test_mailbox@cpscourrier.com')
        else:
            self.assertEquals(doc2['mail_from'], 'foo@foo.com')
        self.assertEquals(doc2['mail_to'], ['bar@foo.com'])

      # common
        attached = getattr(doc2, 'file_f0', None)
        self.failIf(attached is None)
        self.assertEquals(attached.data, 'This is a test')
        attached = getattr(doc2, 'file_1_f0', None)
        self.failIf(attached is None)
        self.assertEquals(attached.data, 'Other foo file')

        # check that they are related
        res = get_original_message_docid(second_reply)
        expected = self.in_mail1.getDocid()
        self.assertEquals(expected, res)

    def test_flag_incoming_answered_1(self):
        wtool = getToolByName(self.portal, 'portal_workflow')
        # the replying scenario with only one reply to in_mail1
        in_mail1 = self.in_mail1
        state = wtool.getInfoFor(self.in_mail1, 'review_state')
        if state == 'received': # Email only
            wtool.doActionFor(in_mail1, 'handle')
        out_mail1 = reply_to_incoming(in_mail1)

        # initial states after creation
        self.assertEquals(self._get_state(in_mail1), 'handled')
        self.assertEquals(self._get_state(out_mail1), 'work')

        # if incoming mail and outgoing mail are not is states 'answering' and
        # 'sent' respectively, this should not change anything
        flag_incoming_answered(out_mail1)
        self.assertEquals(self._get_state(in_mail1), 'handled')
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
        wtool = getToolByName(self.portal, 'portal_workflow')
        state = wtool.getInfoFor(self.in_mail1, 'review_state')
        if state == 'received': # Email only
            wtool.doActionFor(in_mail1, 'handle')
        out_mail1 = reply_to_incoming(in_mail1)
        out_mail2 = reply_to_incoming(in_mail1)

        # initial states after creation
        self.assertEquals(self._get_state(in_mail1), 'handled')
        self.assertEquals(self._get_state(out_mail1), 'work')
        self.assertEquals(self._get_state(out_mail2), 'work')

        # if incoming mail and outgoing mails are not is states 'answering' and
        # 'sent' respectively, this should not change anything
        flag_incoming_answered(out_mail1)
        self.assertEquals(self._get_state(in_mail1), 'handled')
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
        wtool = getToolByName(self.portal, 'portal_workflow')
        state = wtool.getInfoFor(self.in_mail1, 'review_state')
        if state == 'received': # Email only
            wtool.doActionFor(in_mail1, 'handle')
        out_mail1 = reply_to_incoming(in_mail1)
        out_mail2 = reply_to_incoming(in_mail1)
        out_mail3 = reply_to_incoming(in_mail1)
        self._set_state(in_mail1, 'answering')

        # flag_incoming_answered must change the in_mail1 state only if
        # there is only one reply remaining
        flag_incoming_answered(out_mail1)
        self.assertEquals(self._get_state(in_mail1), 'answering')

        # unlink out_mail2, and retry
        unlink(in_mail1, out_mail2)
        flag_incoming_answered(out_mail1)
        self.assertEquals(self._get_state(in_mail1), 'answering')

        # unlink out_mail3, and retry
        unlink(in_mail1, out_mail3)

        # out_mail1 is the last reply: the transition on in_mail1 is
        # triggered
        linked_replies = get_replies_docids(in_mail1)
        self.assertEquals(linked_replies, [out_mail1.getDocid()])
        flag_incoming_handled(out_mail1)
        self.assertEquals(self._get_state(in_mail1), 'handled')


    #
    # the following tests are for workflow scripts but general events.
    # As the setup is similar we reuse them directly
    #

    def test_event_delete_1(self):
        # remove a proxy that is not linked to anything in the relation
        # tool (smoke test)
        in_mail1 = self.in_mail1
        linked_replies = get_replies_docids(in_mail1)
        self.assertEquals(linked_replies, [])
        self.mb.manage_delObjects([in_mail1.getId()])

        # the deletion of other proxies such as the mailbox should produce
        # anything weird either
        self.mbg.manage_delObjects([self.mb.getId()])
        linked_replies = get_replies_docids(in_mail1)
        self.assertEquals(linked_replies, [])

    def test_event_delete_2(self):
        in_mail1 = self.in_mail1
        wtool = getToolByName(self.portal, 'portal_workflow')
        state = wtool.getInfoFor(in_mail1, 'review_state')
        if state == 'received': # Email only
            wtool.doActionFor(in_mail1, 'handle')
        in_mail1_docid = int(in_mail1.getDocid())
        out_mail1 = reply_to_incoming(in_mail1)
        out_mail1_docid = out_mail1.getDocid()

        # out_mail1 is linked has a reply to in_mail1
        linked_replies = get_replies_docids(in_mail1)
        self.assertEquals(linked_replies, [out_mail1_docid])

        # trigger the deletion event
        self.mb.manage_delObjects([out_mail1.getId()])

        # after deletion in_mail1 is no longer linked to anything
        linked_replies = get_replies_docids(in_mail1)
        self.assertEquals(linked_replies, [])

    def test_event_delete_3(self):
        in_mail1 = self.in_mail1
        wtool = getToolByName(self.portal, 'portal_workflow')
        state = wtool.getInfoFor(self.in_mail1, 'review_state')
        if state == 'received': # Email only
            wtool.doActionFor(in_mail1, 'handle')
        in_mail1_docid = int(in_mail1.getDocid())
        out_mail1 = reply_to_incoming(in_mail1)
        out_mail1_docid = out_mail1.getDocid()
        out_mail2 = reply_to_incoming(in_mail1)
        out_mail2_docid = out_mail2.getDocid()

        # out_mail1 and 2 are linked has a reply to in_mail1
        linked_replies = sorted(get_replies_docids(in_mail1))
        expected = sorted((out_mail1_docid, out_mail2_docid))
        self.assertEquals(linked_replies, expected)

        # trigger the deletion event
        self.mb.manage_delObjects([out_mail1.getId()])

        # after deletion in_mail1 is no longer linked to out_mail2
        linked_replies = get_replies_docids(in_mail1)
        self.assertEquals(linked_replies, [out_mail2_docid])

        # deleting the container should delete children and clean the
        # relation graph
        self.mbg.manage_delObjects([self.mb.getId()])
        linked_replies = get_replies_docids(in_mail1)
        self.assertEquals(linked_replies, [])

    def test_event_delete_move(self):
        # smoke test: on proxy move, the relation graph should not change
        in_mail1 = self.in_mail1
        wtool = getToolByName(self.portal, 'portal_workflow')
        state = wtool.getInfoFor(self.in_mail1, 'review_state')
        if state == 'received': # Email only
            wtool.doActionFor(in_mail1, 'handle')
        in_mail1_docid = int(in_mail1.getDocid())
        out_mail1 = reply_to_incoming(in_mail1)
        out_mail1_docid = out_mail1.getDocid()

        # out_mail1 is linked has a reply to in_mail1
        linked_replies = get_replies_docids(in_mail1)
        self.assertEquals(linked_replies, [out_mail1_docid])

        # target mailboxes for moving proxies around
        mb1 = self.mb
        mb2 = self.mb2

        # cut an paste objects at CPS level
        cut = mb1.manage_CPScutObjects([in_mail1.getId()])
        transaction.commit()
        mb2.manage_CPSpasteObjects(cut)
        transaction.commit()

        # relations should not have changed
        linked_replies = get_replies_docids(in_mail1)
        self.assertEquals(linked_replies, [out_mail1_docid])

        # cut an paste objects at Zope level (ZMI for instance)
        cut = mb1.manage_cutObjects([out_mail1.getId()])
        transaction.commit()
        mb2.manage_pasteObjects(cut)
        transaction.commit()

        # relations should not have changed either
        linked_replies = get_replies_docids(in_mail1)
        self.assertEquals(linked_replies, [out_mail1_docid])

    def test_event_delete_checkout(self):
        # smoke test: on checkout draft move, the relation graph should not
        # change
        in_mail1 = self.in_mail1
        wtool = getToolByName(self.portal, 'portal_workflow')
        state = wtool.getInfoFor(self.in_mail1, 'review_state')
        if state == 'received': # Email only
            wtool.doActionFor(in_mail1, 'handle')
        in_mail1_docid = int(in_mail1.getDocid())
        out_mail1 = reply_to_incoming(in_mail1)
        out_mail1_docid = out_mail1.getDocid()
        wtool = getToolByName(self.portal, 'portal_workflow')

        # out_mail1 is linked has a reply to in_mail1
        linked_replies = get_replies_docids(in_mail1)
        self.assertEquals(linked_replies, [out_mail1_docid])

        # create a draft
        wtool.doActionFor(out_mail1, 'checkout_draft',
                          dest_container=self.mb,
                          initial_transition='checkout_draft_in')

        # out_mail1 should still be linked has a reply to in_mail1
        linked_replies = get_replies_docids(in_mail1)
        self.assertEquals(linked_replies, [out_mail1_docid])

        # check draft back in
        draft = self.mb[out_mail1.getId()+'_1']
        wtool.doActionFor(draft, 'checkin_draft',
                          dest_container=self.mb,
                          dest_objects=[out_mail1],
                          checkin_transition="unlock")

        # out_mail1 should still be linked has a reply to in_mail1
        linked_replies = get_replies_docids(in_mail1)
        self.assertEquals(linked_replies, [out_mail1_docid])

    #
    # integration between wf scripts and events
    #

    def test_integration_delete_and_flag_handled(self):
        # test the integration of WF delete events and scripts
        in_mail1 = self.in_mail1
        wtool = getToolByName(self.portal, 'portal_workflow')
        state = wtool.getInfoFor(self.in_mail1, 'review_state')
        if state == 'received': # Email only
            wtool.doActionFor(in_mail1, 'handle')
        out_mail1 = reply_to_incoming(in_mail1)
        out_mail2 = reply_to_incoming(in_mail1)
        out_mail3 = reply_to_incoming(in_mail1)
        self._set_state(in_mail1, 'answering')

        # flag_incoming_answered must change the in_mail1 state only if there is
        # only one reply remaining
        flag_incoming_answered(out_mail1)
        self.assertEquals(self._get_state(in_mail1), 'answering')

        # unlink out_mail1, and retry
        wtool = getToolByName(in_mail1, 'portal_workflow')
        wtool.doActionFor(out_mail1, 'delete')
        self.assertEquals(self._get_state(in_mail1), 'answering')

        # unlink out_mail2, and retry
        wtool.doActionFor(out_mail2, 'delete')
        self.assertEquals(self._get_state(in_mail1), 'answering')

        # unlink out_mail3, flag_handled is automatically triggered
        wtool.doActionFor(out_mail3, 'delete')
        self.assertEquals(self._get_state(in_mail1), 'handled')

    def test_init_stack_with_user(self):
        in_mail = self.in_mail1
        self.login('manager')
        wftool = getToolByName(self.portal, 'portal_workflow')
        # putting in a state where the stack exists
        self._set_state(in_mail, 'handled')

        class FakeStateChange:
            def __init__(self):
                self.kwargs = {}

        sci = FakeStateChange()
        sci.object = in_mail
        sci.workflow = wftool.getWorkflowsFor(in_mail)[0]
        init_stack_with_user(sci, 'Pilots', prefix='courrier_',
                             directive='the_dir')

        stack = wftool.getStackFor(in_mail, 'Pilots')
        self.assertEquals(stack.getAllLevels(), [0])
        elt = stack._getLevelContentValues()[0]
        self.assertEquals(elt['directive'], 'the_dir')

    def test_handle_transition(self):
        in_mail = self.in_mail1
        self.login('manager')
        wftool = getToolByName(self.portal, 'portal_workflow')

        state = wftool.getInfoFor(self.in_mail1, 'review_state')
        if state != 'received':
            # Not an email
            return

        wftool.doActionFor(in_mail, 'handle')

        stack = wftool.getStackFor(in_mail, 'Pilots')
        self.assertEquals(stack.getAllLevels(), [0])
        elt = stack._getLevelContentValues()[0]
        self.assertEquals(elt['directive'], 'handle')
        self.logout()

class WorkflowScriptsPaperIntegrationTestCase(
    PaperIntegrationTestCase,
    WorkflowScriptsIntegrationTestCase):

    def test_reply_to_incoming(self):
        self.in_mail1.getEditableContent().edit(confidential=True,
                                                proxy = self.in_mail1)
        WorkflowScriptsIntegrationTestCase.test_reply_to_incoming(self)
        doc = self.out_mail1.getContent()
        self.assertEquals(self.out_mail1.portal_type, 'Outgoing Pmail')
        self.assertEquals(doc.confidential, True)

    def test_send_reply(self):
        in_mail1 = self.in_mail1
        wtool = getToolByName(self.portal, 'portal_workflow')
        if wtool.getInfoFor(in_mail1, 'review_state') == 'received':
            wtool.doActionFor(in_mail1, 'handle')
        out_mail1 = reply_to_incoming(in_mail1)
        result = send_reply(out_mail1)
        self.assert_(result is None)

    def test_send_html_reply(self):
        pass

    def test_init_stack_with_user(self):
        pass

class WorkflowScriptsEmailIntegrationTestCase(
    WorkflowScriptsIntegrationTestCase):

    def test_reply_to_incoming(self):
        WorkflowScriptsIntegrationTestCase.test_reply_to_incoming(self)
        self.assertEquals(self.outgoing_doc2.portal_type, 'Outgoing Email')

    def test_reply_to_incoming_with_template(self):
        WorkflowScriptsIntegrationTestCase.test_reply_to_incoming_with_template(self)
        doc1 = self.outgoing_doc1
        doc2 = self.outgoing_doc2
        self.assertEquals(sorted(doc2['Subject']()),
                          sorted(("subject1", "subject2",)))
        self.assertEquals(doc2['content'], doc1['content'])

    def test_forward_mail(self):
        # faking the MailHost
        class FakeMailHost:
            def _send(self, *args):
                return args

        encoding = get_final_encoding(self.portal)
        # preparing in_mail1 to get forwarded
        in_mail1 = self.in_mail1
        wtool = getToolByName(self.portal, 'portal_workflow')
        wtool.doActionFor(in_mail1, 'handle')
        in_mail1_doc_edit = in_mail1.getEditableContent()
        in_mail1_doc_edit.edit(
            {'content': "content line 1\ncontent line 2\n"}, proxy=in_mail1,)

        try:
            in_mail1.MailHost = FakeMailHost()

            # ensure the current mailbox has the required 'from' address
            mb_doc = self.mb.getEditableContent()
            mb_doc.edit({'from': 'mailbox@example.com'}, proxy=self.mb)

            # forwdaring in_mail1
            result = forward_mail(in_mail1, 'toto@example.com',
                                  comment='Please handle that request')
            expected = ('mailbox@example.com', ['toto@example.com'], """\
Content-Type: text/plain; charset="%s"
MIME-Version: 1.0
Content-Transfer-Encoding: quoted-printable
Subject: Fwd: Test mail 1
From: mailbox@example.com
To: toto@example.com

Please handle that request

On %s, bar@foo.com wrote:
> content line 1
> content line 2
>=20\
""" % (encoding, datetime.datetime.now().strftime('%Y-%m-%d')))

            self.assertEquals(result, expected)
        finally:
            # for some reason there is a ZODB commit in beforeTearDown thus
            # we need get rid of the unpickleable fake MailHost
            del in_mail1.MailHost

    def test_send_reply(self):
        # faking the MailHost
        class FakeMailHost:
            def _send(self, *args):
                return args

        encoding = get_final_encoding(self.portal)

        in_mail1 = self.in_mail1
        wtool = getToolByName(self.portal, 'portal_workflow')
        wtool.doActionFor(in_mail1, 'handle')
        in_mail1_doc_edit = in_mail1.getEditableContent()
        in_mail1_doc_edit.edit({
            'content': "Hi!\nPlease go to http://www.paipal.com and confirm"
                       " your password!\n  Regards,\n  The Paipal team"},
            proxy=in_mail1,
        )
        out_mail1 = reply_to_incoming(in_mail1)
        try:
            out_mail1.MailHost = FakeMailHost()
            out_mail1_doc_edit = out_mail1.getEditableContent()
            out_mail1_doc_edit.edit(
                mail_cc=["bar2@foo.com"],
                content="Please stop trying to fish us!",
                content_format='text',
                form_of_address='regards',
                proxy=out_mail1,
            )

            result = send_reply(out_mail1)
            expected = ('test_mailbox@cpscourrier.com', ['bar@foo.com'], """\
Content-Type: text/plain; charset="%s"
MIME-Version: 1.0
Content-Transfer-Encoding: quoted-printable
Subject: Re: Test mail 1
From: test_mailbox@cpscourrier.com
To: bar@foo.com
Cc: bar2@foo.com

Please stop trying to fish us!

Best regards, =


-- =

CPS Manager


On %s, bar@foo.com wrote:
> Hi!
> Please go to http://www.paipal.com and confirm your password!
>   Regards,
>   The Paipal team""" % (encoding, datetime.datetime.now().strftime('%Y-%m-%d')))

            self.assertEquals(result, expected)
        finally:
            # for some reason there is a ZODB commit in beforeTearDown thus we
            # need get rid of the unpickleable fake MailHost
            del out_mail1.MailHost

        # check that the sending date has been set
        doc = out_mail1.getContent()
        dm = doc.getTypeInfo().getDataModel(doc)
        eff_date = dm['EffectiveDate']
        time_delta = DateTime() - eff_date
        self.failIf(time_delta > 10) # should be close enough

    def test_send_html_reply(self):
        # faking the MailHost
        class FakeMailHost:
            def _send(self, *args):
                return args

        encoding = get_final_encoding(self.portal)
        in_mail1 = self.in_mail1
        wtool = getToolByName(self.portal, 'portal_workflow')
        wtool.doActionFor(in_mail1, 'handle')
        in_mail1_doc_edit = in_mail1.getEditableContent()
        in_mail1_doc_edit.edit({
            'content': "Hi!\nPlease go to http://www.paipal.com and confirm"
                       " your password!\n  Regards,\n  The Paipal team"},
            proxy=in_mail1,
        )
        out_mail1 = reply_to_incoming(in_mail1)
        try:
            out_mail1.MailHost = FakeMailHost()
            out_mail1_doc_edit = out_mail1.getEditableContent()
            out_mail1_doc_edit.edit(
                mail_cc=["Toto Truc <toto-truc@fake.org>", "og@nuxeo.com"],
                content="<em>Please</em> stop trying to fish us!",
                content_format='html',
                form_of_address='regards',
                proxy=out_mail1,
            )

            result = send_reply(out_mail1)
            expected = ('test_mailbox@cpscourrier.com', ['bar@foo.com'], """\
Content-Type: text/html; charset="%s"
MIME-Version: 1.0
Content-Transfer-Encoding: quoted-printable
Subject: Re: Test mail 1
From: test_mailbox@cpscourrier.com
To: bar@foo.com
Cc: Toto Truc <toto-truc@fake.org>, og@nuxeo.com

<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
  <meta content=3D"text/html;charset=3D%s" http-equiv=3D"Content-T=
ype">
  <title></title>
</head>
<body bgcolor=3D"#ffffff" text=3D"#000000"><em>Please</em> stop trying to f=
ish us!<br/><br/>Best regards, <br/><br/>-- <br/>CPS Manager<br/>
<pre>

On %s, bar@foo.com wrote:
> Hi!
> Please go to http://www.paipal.com and confirm your password!
>   Regards,
>   The Paipal team</pre>
</body>
</html>""" % (encoding, encoding.upper(), datetime.datetime.now().strftime('%Y-%m-%d')))

            dummy = """ " """ # for Emacs editor

            self.assertEquals(result[0], expected[0])
            self.assertEquals(result[1], expected[1])
            ### XXX GR regexp is bogus, will correct later
            self.assert_(re.sub(r'====.+==', '====(boundary)==', result[2]),
                         expected[2])
        finally:
            # for some reason there is a ZODB commit in beforeTearDown thus we
            # need get rid of the unpickleable fake MailHost
            del out_mail1.MailHost


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(WorkflowScriptsEmailIntegrationTestCase),
        unittest.makeSuite(WorkflowScriptsPaperIntegrationTestCase),
        ))
