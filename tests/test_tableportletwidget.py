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
from Products.CPSDefault.tests.CPSTestCase import CPSTestCase

from CPSCourrierIntegrationTestCase import CPSCourrierLayer
from Products.CPSSchemas.tests.testWidgets import FakeDataStructure
from Products.CPSCourrier.braindatamodel import FakeBrain


# things to be tested
from Products.CPSSchemas.DataStructure import DataStructure
from Products.CPSSchemas.Widget import widgetRegistry
from Products.CPSDocument.FlexibleTypeInformation import FlexibleTypeInformation
from Products.CPSCourrier.widgets.tableportletwidget import TabularPortletWidget


class TestingTabPortletWidget(TabularPortletWidget):
    """ A subclass to implement listItems. """

    brains = [FakeBrain(d) for d in [
        {'Title' : 'Title 1', 'Description' : 'Pending'},
        {'Title' : 'Title 2', 'Description' : 'Rejected'},
        ]]

    def listItems(self):
        return self.brains 
    
class IntegrationTestTablePortlet(CPSTestCase):

    layer = CPSCourrierLayer

    def afterSetUp(self):
        self.login('manager')

        # a portlet widget
        self.widget = TestingTabPortletWidget('the_id')
        self.widget.manage_changeProperties(row_layout='test_row')

        # a portlet context for the widget
        ptltool = self.portal.portal_cpsportlets
        ptl_id = ptltool.createPortlet(ptype_id='Test Tabular Portlet',
                                       context=self.portal,
                                       slot='slot',
                                       order=1)
        portlets_container = ptltool.getPortletContainer(
            context=self.portal)
        portlet = portlets_container.getPortletById(ptl_id)
        self.portlet = portlet

        dm = self.portlet.getTypeInfo().getDataModel(portlet, context=portlet)
        self.ds = DataStructure(datamodel=dm)

    def beforeTearDown(self):
        ## TODO: remove portlet 
        pass
    
    def test_widget_registration(self):
        self.assert_(
            'Tabular Portlet Widget' in widgetRegistry.listWidgetMetaTypes())

    def test_layer(self):
        # some of these can be discarded to get more flexibility back
        layout_tool = self.portal.portal_layouts
        ptl_layout = getattr(layout_tool, 'test_portlet', None)
        self.failIf(ptl_layout is None)

        ptl_wi = getattr(ptl_layout, 'w__portlet', None)
        self.failIf(ptl_wi is None)
        self.assertEquals(ptl_wi.row_layout, 'test_row')

    def test_view_render(self):
        rendered = self.widget.render('view', self.ds)

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(IntegrationTestTablePortlet),
        doctest.DocTestSuite('Products.CPSCourrier.widgets.tableportletwidget'),
        ))
