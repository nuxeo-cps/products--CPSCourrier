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
from Products.CPSCourrier.workflows.scripts import reply_to_incoming

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

    def test_reply_to_incoming(self):
        # add 'Re:' to the incoming mail title
        out_mail1 = reply_to_incoming(self.in_mail1)
        self.assertEquals(out_mail1.Title(), 'Re: Test mail 1')
        doc1 = out_mail1.getContent()
        self.assertEquals(doc1['from'], 'test_mailbox@cpscourrier.com')
        self.assertEquals(doc1['to'], ['bar@foo.com'])

        # do not add the 'Re:' prefix twice
        out_mail2 = reply_to_incoming(self.in_mail2)
        doc2 = out_mail2.getContent()
        self.assertEquals(out_mail2.Title(), 'Re: Test mail 1')
        self.assertEquals(doc2['from'], 'test_mailbox@cpscourrier.com')
        self.assertEquals(doc2['to'], ['foo@foo.com'])



def test_suite():
    return unittest.makeSuite(WorkflowScriptsIntegrationTestCase)
