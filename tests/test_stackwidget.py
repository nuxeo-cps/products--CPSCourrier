# (C) Copyright 2005 Nuxeo SARL <http://nuxeo.com>
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
# $Id$
"""Test stack widget"""

import unittest
import unittest
from zope.testing.doctest import DocFileTest

from Products.CPSSchemas.tests.testWidgets import (
    FakeDataModel, FakeDataStructure, fakePortal,
    )
from Products.CPSWorkflow.stack import Stack
from Products.CPSCourrier.widgets.stackwidget import CPSStackWidget

class FakeWorkflowTool:
    
    def cookAttr(self, var):
        return '_fake_wftool_' + var
    
    def getInfoFor(self, ob, var):
        try: 
            return getattr(ob, self.cookAttr(var))
        except AttributeError:
            raise KeyError(var)
        
    def setInfoFor(self, ob, var, value): 
        setattr(ob, self.cookAttr(var), value)
                      
fakePortal.portal_workflow = FakeWorkflowTool()

class FakeStack(Stack):

    def render(self, mode, context):
        self.last_render = (mode, context)

class FakeProxy:
    pass

class TestStackWidget(unittest.TestCase):

    def test_getContext(self):
        widget = CPSStackWidget('spam')
        dm = FakeDataModel()
        dm.proxy = 'someproxy'
        ds = FakeDataStructure(dm)

        self.assertEquals(widget.getContext(ds), 'someproxy')

    def test_render(self):
        proxy = FakeProxy()
        wftool = fakePortal.portal_workflow
        stack = FakeStack()
        wftool.setInfoFor(proxy, 'stackvarid', stack)
        wftool.setInfoFor(proxy, 'other', 1)

        dm = FakeDataModel()
        dm.proxy = proxy
        ds = FakeDataStructure(dm)

        widget = CPSStackWidget('spam').__of__(fakePortal)
        widget.stack_var_id = 'stackvarid'

        widget.render('render_mode', ds)
        self.assertEquals(stack.last_render, ('render_mode', proxy))

        # this one relies too much on the fake workflow tool
        widget.stack_var_id = 'nonexistent'
        self.assertRaises(RuntimeError, widget.render, 'view', ds)

        widget.stack_var_id = 'other'
        self.assertRaises(ValueError, widget.render, 'view', ds)
        

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(TestStackWidget),
        ))

if __name__ == '__main__':
    unittest.TextTestRunner().run(test_suite())
