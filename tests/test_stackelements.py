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
from Products.CPSCourrier.workflows.stackelements import (
    UserStackElementWithData,
    )

class UserStackElementWithDataIntegrationTestCase(CPSTestCase):

    layer = CPSCourrierLayer

    def afterSetUp(self):
        dtool = getToolByName(self.portal, 'portal_directories')
        mdir = dtool.members

        mdir._createEntry({'id': 'testuser',
                           'roles' : ['Member',]})

        self.elt = UserStackElementWithData('user_wdata:testuser')

    def test_holdsCurrentMember(self):
        self.login('testuser')
        self.assert_(self.elt.holdsCurrentMember(self.portal))

        self.login('manager')
        self.failIf(self.elt.holdsCurrentMember(self.portal))


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(UserStackElementWithDataIntegrationTestCase),
        doctest.DocFileTest('doc/developer/stackelements.txt',
                            package='Products.CPSCourrier',
                            optionflags=doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS),
        ))
