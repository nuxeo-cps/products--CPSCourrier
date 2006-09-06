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

# testing module and harness

import unittest
from zope.testing import doctest

from Products.CPSCourrier.tests.layer import CourrierPaperFunctionalTestCase
from Products.CPSCourrier.directoryutils import hasLocalAddressBookRole


class FunctionalDirectoryUtilsTestCase(CourrierPaperFunctionalTestCase):

    def test_hasLocalAddressBookRole(self):
        mb_doc= self.mb.getContent()
        def has(role):
            return hasLocalAddressBookRole(self.portal, mb_doc.ou, role)

        self.flogin('reader', self.mb)
        self.assert_(has('Reader'))
        self.failIf(has('Contributor'))
        self.failIf(has('LocalManager'))

        self.flogin('member1', self.mb)
        self.failIf(has('Reader'))
        self.assert_(has('Contributor'))
        self.failIf(has('LocalManager'))

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(FunctionalDirectoryUtilsTestCase),
        ))
