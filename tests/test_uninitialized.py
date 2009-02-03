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
# $Id$
"""Test cases to check that CPSCourrier does not break the rest of 
CPS if present but its profiles haven't been imported."""

import unittest

from Testing import ZopeTestCase

from Products.CPSDefault.tests.CPSTestCase import CPSTestCase

ZopeTestCase.installProduct('CPSRelation')

class UninitializedCPSCourrierTestCase(CPSTestCase):

    def testWithRelations(self):
        # See #1967

        setup_tool = self.portal.portal_setup
        setup_tool.setImportContext('profile-%s' % 'CPSRelation:default')
            
        setup_tool.runAllImportSteps()

        wftool = self.portal.portal_workflow
        ws = self.portal.workspaces
        self.login('manager')
        wftool.invokeFactoryFor(ws, "File", 'a_file')
        
        # here starts the actual testing. Used to raise
        ws.manage_delObjects(['a_file'])

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(UninitializedCPSCourrierTestCase),
        ))

