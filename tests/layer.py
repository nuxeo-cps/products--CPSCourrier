# Copyright (c) 2006 Nuxeo SAS <http://nuxeo.com>
# Author : Georges Racinet <gracinet@nuxeo.com>
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

import transaction
import unittest
from zope.testing import doctest
from Testing import ZopeTestCase
from Products.GenericSetup import profile_registry
from Products.GenericSetup import EXTENSION
from Products.CMFCore.utils import getToolByName
from Products.CPSCore.interfaces import ICPSSite


from Products.CPSSchemas.tests.testWidgets import (
    FakeDataModel, FakeDataStructure, fakePortal,
    )
from Products.CPSDefault.tests.CPSTestCase import (
    CPSTestCase,
    ExtensionProfileLayerClass)

from Products.CPSCourrier.tests import widgets, stackelements
from Products.CPSCourrier.config import RELATION_GRAPH_ID


# register profiles
ZopeTestCase.installProduct('CPSCourrier')
ZopeTestCase.installProduct('CPSRelation')

# CPSCourrier:tests : add more layouts to test the widgets
profile_registry.registerProfile(
    'tests',
    'CPS Courrier Tests',
    "Tests of mail tracking and management system for CPS",
    'tests/profile',
    'CPSCourrier',
    EXTENSION,
    for_=ICPSSite)


class CPSCourrierLayerClass(ExtensionProfileLayerClass):
    extension_ids = ('CPSCourrier:default', 'CPSCourrier:tests',)

CPSCourrierLayer = CPSCourrierLayerClass(
    __name__,
    'CPSCourrierLayer'
    )

class IntegrationTestCase(CPSTestCase):
    layer = CPSCourrierLayer
    MBG_ID = 'test-mailbox-group'
    MB_ID = 'test-mailbox'
    MB2_ID = 'test-mailbox2'

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

        wftool.invokeFactoryFor(self.mbg, 'Mailbox', self.MB2_ID,
                                **{'from': 'test_mailbox2@cpscourrier.com'})
        self.mb2 = self.mbg[self.MB2_ID]

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

        # this is required for cut/paste integration tests
        transaction.commit()

    def beforeTearDown(self):
        # ensure the catalog is clean
        self.portal.portal_catalog.refreshCatalog(clear=1)
        # ensure the graph is clean
        self.portal.portal_relations.removeAllRelationsFor(
            RELATION_GRAPH_ID, int(self.in_mail1.getDocid()))
        self.portal.portal_relations.removeAllRelationsFor(
            RELATION_GRAPH_ID, int(self.in_mail2.getDocid()))
        # delete the test areas
        self.portal.mailboxes.manage_delObjects([self.MBG_ID])
        transaction.commit()
        self.logout()

    # make tests less verbose by using custom accessor for WF state
    def _get_state(self, ob):
        return ob.workflow_history.values()[0][-1]['review_state']

    def _set_state(self, ob, state):
        ob.workflow_history.values()[0][-1]['review_state'] = state


