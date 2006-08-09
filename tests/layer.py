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
from AccessControl import getSecurityManager
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

from Products.CPSCourrier.tests import stackelements
from Products.CPSCourrier.config import RELATION_GRAPH_ID


# register profiles
ZopeTestCase.installProduct('CPSDashboards')
ZopeTestCase.installProduct('CPSCourrier')
ZopeTestCase.installProduct('CPSRelation')

class CPSCourrierLayerClass(ExtensionProfileLayerClass):
    extension_ids = ('CPSCourrier:default', 'CPSCourrier:email',
                     'CPSCourrier:paper')

CPSCourrierLayer = CPSCourrierLayerClass(
    __name__,
    'CPSCourrierLayer'
    )

class CommonIntegrationFixture:
    """ Things like site structure and such."""

    def fixtureSetUp(self):
        # create test sandboxes in the mailboxes space
        self.wftool = wftool = getToolByName(self.portal, 'portal_workflow')
        self.ttool = ttool = getToolByName(self.portal, 'portal_types')
        mailboxes = self.portal.mailboxes

        wftool.invokeFactoryFor(mailboxes, 'Mailbox Group', self.MBG_ID)
        self.mbg = mailboxes[self.MBG_ID]

        wftool.invokeFactoryFor(self.mbg, 'Mailbox', self.MB_ID,
                                **{'from': 'test_mailbox@cpscourrier.com'})
        self.mb = self.mbg[self.MB_ID]

        wftool.invokeFactoryFor(self.mbg, 'Mailbox', self.MB2_ID,
                                **{'from': 'test_mailbox2@cpscourrier.com'})
        self.mb2 = self.mbg[self.MB2_ID]

    # make tests less verbose by using custom accessor for WF state
    def _get_state(self, ob):
        return ob.workflow_history.values()[0][-1]['review_state']

    def _set_state(self, ob, state):
        ob.workflow_history.values()[0][-1]['review_state'] = state


class CPSCourrierFunctionalLayerClass(CommonIntegrationFixture,
                                      CPSCourrierLayerClass):

    """Functional testing layer.

    The contract of testcases living in this layer is that they must
    create their mail documents and clean up their mess. """

    #can't use __bases__ here, since method names change

    MBG_ID = 'ftest-mailbox-group'
    MB_ID = 'ftest-mailbox'
    MB2_ID = 'ftest-mailbox2'

    def setUp(self):
        CPSCourrierLayerClass.setUp(self)
        self.login()
        CommonIntegrationFixture.fixtureSetUp(self)
        # create some users
        mtool = getToolByName(self.portal, 'portal_membership')
        dtool = getToolByName(self.portal, 'portal_directories')
        mdir = dtool['members']

        roles = {'reader': 'Reader',
                 'member1': 'Contributor',
                 'member2': 'Contributor',
                 'member3': 'Contributor',
                 'injector': 'Injector',
                 'wsmanager': 'LocalManager',}
        for prefix, role in roles.items():
            for id, folder in ((self.MBG_ID, self.mbg,),
                               (self.MB_ID, self.mb,),
                               (self.MB2_ID, self.mb2,)):
                user_id = '%s_%s' % (prefix, id)
                mdir._createEntry({'id': user_id, 'roles':('Member',)})
                mtool.setLocalRoles(folder, [user_id], role)
        transaction.commit()
        self.logout()

    def tearDown(self):
        pass


CPSCourrierFunctionalLayer = CPSCourrierFunctionalLayerClass(
    __name__,
    'CPSCourrierFunctionalLayer'
    )


class IntegrationTestCase(CommonIntegrationFixture, CPSTestCase):
    """For tests that need to avoid side-effects.

    provides the same kind of environment as CPSCourrierFunctionalLayer.
    doesn't share anything but profiles."""

    layer = CPSCourrierLayer

    MBG_ID = 'test-mailbox-group'
    MB_ID = 'test-mailbox'
    MB2_ID = 'test-mailbox2'

    INCOMING_PTYPE = 'Incoming Email'
    INITIAL_TRANSITION = 'create'
    
    def afterSetUp(self):
        self.login('manager')
        CommonIntegrationFixture.fixtureSetUp(self)
        # add some incoming mails
        incoming_mail_data = {
            'in_mail1': {
                'Title': 'Test mail 1',
                'mail_to': ['foo@foo.com'],
                'mail_cc': ['foo1@foo.com', 'foo2@foo.com'],
                'mail_from': 'bar@foo.com',
            },
            'in_mail2': {
                'Title': 'Re: Test mail 1',
                'mail_to': ['bar2@foo.com', 'toto@email.com'],
                'mail_cc': ['bar1@foo.com', 'bar2@foo.com'],
                'mail_from': 'foo@foo.com',
            },
        }
        for mail_id, mail_data in incoming_mail_data.items():
            self.wftool.invokeFactoryFor(self.mb, self.INCOMING_PTYPE, mail_id,
                                         initial_transition=\
                                                       self.INITIAL_TRANSITION,
                                         **mail_data)
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

class PaperIntegrationTestCase(IntegrationTestCase):
    INCOMING_PTYPE = 'Incoming Pmail'
    INITIAL_TRANSITION = 'create'

class CourrierFunctionalTestCase(CPSTestCase):

    layer = CPSCourrierFunctionalLayer

    def afterSetUp(self):
        self.mbg = getattr(self.portal.mailboxes, self.layer.MBG_ID)
        self.mb = getattr(self.mbg, self.layer.MB_ID)
        self.mb2 = getattr(self.mbg, self.layer.MB2_ID)
        self.wftool = getToolByName(self.portal, 'portal_workflow')
        self.ttool = getToolByName(self.portal, 'portal_types')

    def flogin(self, prefix, object):
        """ Login as prefixed user on object.

        Typical use case: self.flogin('member1', self.mb) logs in as
        one of the users that were created in layer to be Contributor in
        self.mb.
        """
        self.login('%s_%s' % (prefix, object.getId()))


    def createIncoming(self, container=None, mail_id='incoming'):
        """Create incoming mail and set it as an attr on self.

        Default container is self.mb,
        """
        self.createMail(container=container,
                        mail_id=mail_id,
                        portal_type="Incoming Email")

    def createOutgoing(self, container=None, mail_id='outgoing'):
        """Create outgoing mail and set it as an attr on self.

        Default container is self.mb,
        """
        self.createMail(container=container,
                        mail_id=mail_id,
                        portal_type="Outgoing Email")

    def createMail(self, container=None, mail_id=None, portal_type=None):
        """Create mail and set it as an attr on self using given id

        Default container is self.mb
        """
        if container is None:
            container = self.mb

        mail_id = self.wftool.invokeFactoryFor(self.mb,
                                               portal_type,
                                               mail_id,
                                               initial_transition='create'
                                               )

        mail = container[mail_id]
        setattr(self, mail_id, mail)
        setattr(self, '%s_id' % mail_id, mail.getId())

    def getRolesFor(self, object):
        """ Return roles for current user, and for everybody.
        """

        pm = getToolByName(self.portal, 'portal_membership')
        roles = pm.getMergedLocalRoles(object)
        user_id = getSecurityManager().getUser().getId()
        return roles, roles.get('user:%s' %user_id)

    # make tests less verbose by using custom accessor for WF state
    def _get_state(self, ob):
        return ob.workflow_history.values()[0][-1]['review_state']

    def _set_state(self, ob, state):
        ob.workflow_history.values()[0][-1]['review_state'] = state

