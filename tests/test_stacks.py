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
from Products.CPSDefault.tests.CPSTestCase import CPSTestCase
from layer import CPSCourrierLayer

from Products.CMFCore.utils import getToolByName
from Products.CPSSchemas.DataModel import DataModel
from Products.CPSCourrier.workflows.stacks import HierarchicalStackWithData

class HierarchicalStackWithDataIntegrationTestCase(CPSTestCase):

    layer = CPSCourrierLayer

    def afterSetUp(self):
        self.login('manager')
        self.stack = HierarchicalStackWithData()

        # Some content, necessary for wf checks
        self.mailboxes = self.portal.mailboxes
        wftool = getToolByName(self.portal, 'portal_workflow')

        mboxgrp_id = wftool.invokeFactoryFor(self.mailboxes, 'Mailbox Group',
                                             'mbox_group')
        self.mbox_group = self.mailboxes[mboxgrp_id]

        mbox_id = wftool.invokeFactoryFor(self.mbox_group, 'Mailbox Group',
                                          'mbox')
        self.mbox = self.mbox_group[mbox_id]

        dm = DataModel(None)
        outgoing_id = wftool.invokeFactoryFor(self.mbox, 'Outgoing Mail',
                                          'outgoing_mail', datamodel=dm)
        self.outgoing_mail = self.mbox[outgoing_id]

    def test_getStackContentForRender(self):
        self.stack.push(push_ids=('example:A', 'example:B'),
                        levels=(0,1,),
                        data_lists=('d1', 'd2'),
                        d1=('A1', 'B1',),
                        d2=('A2', 'B2',))

        extr = self.stack.getStackContentForRender(self.outgoing_mail,
                                                   mode='view')
        # TODO: assertions



def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(HierarchicalStackWithDataIntegrationTestCase),
        doctest.DocFileTest('doc/developer/stacks.txt',
                            package='Products.CPSCourrier',
                            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS),
        ))
