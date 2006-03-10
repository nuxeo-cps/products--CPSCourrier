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

""" This module defines some concrete widget implementations for base classes
that will be loaded via test profile in the CPSCourrier test layer.

Therefore they have to be outside of integration test modules."""

from Globals import InitializeClass

from Products.CPSSchemas.Widget import widgetRegistry
from Products.CPSSchemas.DataStructure import DataStructure

from Products.CPSCourrier.braindatamodel import FakeBrain, BrainDataModel
from Products.CPSCourrier.widgets.tabular import TabularWidget


class TestingTabularWidget(TabularWidget):
    """ A subclass to implement listRowDataStructures. """

    meta_type = 'Testing Tabular Widget'

    brains = [FakeBrain(d) for d in [
        {'Title' : 'Title 1', 'content' : 'Pending', 'Description' : '',},
        {'Title' : 'Title 2', 'content' : 'Rejected', 'Description' : '',},
        ]]

    def listRowDataStructures(self, datastructure, row_layout, **kw):
        gendss = (DataStructure(datamodel=BrainDataModel(brain))
                              for brain in self.brains)
        return (self.prepareRowDataStructure(row_layout, ds) for ds in gendss)

InitializeClass(TestingTabularWidget)
widgetRegistry.register(TestingTabularWidget)
