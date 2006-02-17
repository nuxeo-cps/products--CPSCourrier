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
from Products.CPSCourrier.widgets.foldercontentsportletwidget import FolderContentsPortletWidget


class TestingTabPortletWidget(TabularPortletWidget):
    """ A subclass to implement listRowDataModels. """

    brains = [FakeBrain(d) for d in [
        {'Title' : 'Title 1', 'Description' : 'Pending'},
        {'Title' : 'Title 2', 'Description' : 'Rejected'},
        ]]

    def listRowDataModels(self, datastructure, **kw):
        return (BrainDataModel(brain) for brain in self.brains)


class CustomMethodsWidget:
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
        

class TestingTabPortletWidgetCustomMethods(CustomMethodsWidget,
                                           TestingTabPortletWidget):
    pass


class IntegrationTestCase(CPSTestCase):

    layer = CPSCourrierLayer

    def afterSetUp(self):
        self.login('manager')

        # a common datastructure for portlet widget tests
        ptltool = self.portal.portal_cpsportlets
        self.ptl_id = ptltool.createPortlet(ptype_id='Test Tabular Portlet',
                                       context=self.portal,
                                       slot='slot',
                                       order=1)
        portlets_container = ptltool.getPortletContainer(
            context=self.portal)
        portlet = portlets_container.getPortletById(self.ptl_id)
        self.portlet = portlet
        dm = self.portlet.getTypeInfo().getDataModel(portlet, context=portlet)
        self.ds = DataStructure(datamodel=dm)

        self.afterAfterSetUp()

    def beforeTearDown(self):
        ## TODO: remove portlet
        pass

#
# Generic Tabular Portlet Widget
#

class IntegrationTestTabularPortlet(IntegrationTestCase):

    def afterAfterSetUp(self):
        # a portlet widget with custom rendering methods
        self.widget = TestingTabPortletWidgetCustomMethods(
            'the_id_custom')
        self.widget.manage_changeProperties(row_layout='test_row')

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

    def test_render_layout_default_view(self):
        # layout render context will be the usual one
        widget = TestingTabPortletWidget('the_id')
        widget.manage_changeProperties(row_layout='test_row')

        rendered = widget.render('view', self.ds)

    def test_render_view(self):
        rendered = self.widget.render('view', self.ds)
        self.assertEquals(rendered.split('\n'), [
            'Title 1|<div class="ddefault">Pending</div>',
            'Title 2|<div class="ddefault">Rejected</div>',
            ])

    def test_vidget_render_method(self):
        # call the widget with our testing render_method
        self.widget.render_method = 'widget_render_method'
        rendered = self.widget.render('view', self.ds)

        # retrieved what was passed to the render method
        columns = self.widget.passed_columns
        rows = self.widget.passed_rows

        # rows hold the rendering of each item
        self.assert_(rows[0].find('Title 1') != -1)
        self.assert_(rows[1].find('Title 2') != -1)

        # columns hold the widget objects
        self.assert_(columns[0].meta_type == 'String Widget')
        self.assert_(columns[0].getId() == 'w__Title')

        self.assert_(columns[1].meta_type == 'Text Widget')
        self.assert_(columns[1].getId() == 'w__Description')

#
# Sub classes
#

class TestingFolderContentsPortletWidget(CustomMethodsWidget,
                                         FolderContentsPortletWidget):
    pass


class IntegrationTestFolderContents(IntegrationTestCase):

    def afterAfterSetUp(self):
        self.widget = TestingFolderContentsPortletWidget('the widget')
        self.widget.manage_changeProperties(row_layout='test_row')
        
    def test_folder_contents(self):
        # creating some content to list
        wftool = self.portal.portal_workflow
        container = self.portal.workspaces
        item1 = wftool.invokeFactoryFor(container, 'News Item', 'item1',
                                        Title='Title 1',
                                        Description='Description 1')

        item2 = wftool.invokeFactoryFor(container, 'News Item', 'item2',
                                        Title='Title 2',
                                        Description='Description 2')

        rendered = self.widget.render('view', self.ds, context_obj=container)
        self.assertEquals(rendered.split('\n'), [
            'Title 1|<div class="ddefault">Description 1</div>',
            'Title 2|<div class="ddefault">Description 2</div>',
            ])
        


def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(IntegrationTestTabularPortlet),
        unittest.makeSuite(IntegrationTestFolderContents),
        doctest.DocTestSuite('Products.CPSCourrier.widgets.tableportletwidget'),
        ))
