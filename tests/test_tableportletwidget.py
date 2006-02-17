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
from Products.CPSCourrier.braindatamodel import FakeBrain, BrainDataModel


# things to be tested
from Products.CPSSchemas.DataStructure import DataStructure
from Products.CPSSchemas.Widget import widgetRegistry
from Products.CPSDocument.FlexibleTypeInformation import FlexibleTypeInformation
from Products.CPSCourrier.widgets.tableportletwidget import TabularPortletWidget


class TestingTabPortletWidget(TabularPortletWidget):
    """ A subclass to implement listRowDataModels. """

    brains = [FakeBrain(d) for d in [
        {'Title' : 'Title 1', 'Description' : 'Pending'},
        {'Title' : 'Title 2', 'Description' : 'Rejected'},
        ]]

    def listRowDataModels(self, datastructure, **kw):
        return (BrainDataModel(brain) for brain in self.brains)

class TestingTabPortletWidgetCustomMethods(TestingTabPortletWidget):
    """ A subclass that make use custom variants of layout_xxx methods."""

    # attributes for introspection after method calls
    last_render_call = None
    passed_rows = None
    passed_columns = None

    def getMethodContext(self, datastructure):
        return self

    def clearHistory(self):
        self.last_render_call = None

    def layout_default_view(self, layout=None, **kw):
        self.last_called = 'view'
        return '|'.join([row[0]['widget_rendered']
                          for row in layout['rows']]
                         )
    def widget_render_method(self, columns=None, rows=None, **kw):
        # deepcopy would not work
        # (Can't pickle objects in acquisition wrappers.) 
        self.passed_columns = columns 
        self.passed_rows = rows
        

class IntegrationTestTablePortlet(CPSTestCase):

    layer = CPSCourrierLayer

    def afterSetUp(self):
        self.login('manager')

        # a portlet widget
        self.widget = TestingTabPortletWidget('the_id')
        self.widget.manage_changeProperties(row_layout='test_row')

        # one with custom methods
        self.widget_custom = TestingTabPortletWidgetCustomMethods(
            'the_id_custom')
        self.widget_custom.manage_changeProperties(row_layout='test_row')

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
        # Check that there's no problem with standard layout_view
        rendered = self.widget.render('view', self.ds)

    def test_view_render_custom(self):
        # Check with custom layout methods
        rendered = self.widget_custom.render('view', self.ds)
        self.assertEquals(rendered.split('\n'), [
            'Title 1|<div class="ddefault">Pending</div>',
            'Title 2|<div class="ddefault">Rejected</div>',
            ])

    def test_vidget_render_method(self):
        # call the widget with our testing render_method
        self.widget_custom.render_method = 'widget_render_method'
        rendered = self.widget_custom.render('view', self.ds)

        # retrieved what was passed to the render method
        columns = self.widget_custom.passed_columns
        rows = self.widget_custom.passed_rows

        # rows hold the rendering of each item
        self.assert_(rows[0].find('Title 1') != -1)
        self.assert_(rows[1].find('Title 2') != -1)

        # columns hold the widget objects
        self.assert_(columns[0].meta_type == 'String Widget')
        self.assert_(columns[0].getId() == 'w__Title')

        self.assert_(columns[1].meta_type == 'Text Widget')
        self.assert_(columns[1].getId() == 'w__Description')
        

def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(IntegrationTestTablePortlet),
        doctest.DocTestSuite('Products.CPSCourrier.widgets.tableportletwidget'),
        ))
