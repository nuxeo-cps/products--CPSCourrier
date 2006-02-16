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
# $Id$


""" Portlet Widgets. """

from copy import deepcopy

from zLOG import LOG, DEBUG
from Globals import InitializeClass

from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.Widget import CPSWidget
from Products.CPSSchemas.Widget import widgetRegistry
from Products.CPSSchemas.DataModel import DataModel
from Products.CPSSchemas.DataStructure import DataStructure

from Products.CPSPortlets.CPSPortletWidget import CPSPortletWidget

from Products.CPSCourrier.braindatamodel import BrainDataModel

class TabularPortletWidget(CPSPortletWidget):
    """ A generic portlet widget to display tabular contents.

    Uses a layout to apply on search results (brains). If flexible, this
    layout is attached to the portlet.
    >>> wi = TabularPortletWidget('spam')
    """

    meta_type = "Tabular Portlet Widget"

    _properties = _properties = CPSPortletWidget._properties + (
        {'id': 'row_layout', 'type': 'string', 'mode': 'w',
         'label': 'Layout to use for the rows', 'is_required' : 1},
        )

    row_layout = '' # handy for tests

    def listItems(self):
        """To be implemented by subclasses.

        Returns brains or objects according to the type of query one
        might want to implement.
        """
        raise NotImplementedError

    def getPortlet(self, datastructure):
        return datastructure.getDataModel().getObject()

    def getMethodContext(self, datastructure):
        """Return the context from where to lookup the layout rendering method.

        Override this if you want to replace a slow zpt parsing by fixed python
        code. 

        To do this for widgets would require to pass the context at
        datastructure init time.
        """
        
        return datastructure.getDataModel().getContext()
    
    def render(self, mode, datastructure, **kw):
        portlet = self.getPortlet(datastructure)

        lid = self.row_layout
        fti = portlet.getTypeInfo()
        layout_structures = fti._computeLayoutStructures(
            datastructure, 'view', layout_id=lid, ob=portlet)
        # maybe can be fetched from the layout structures as well (perf)
        row_layout = fti.getLayout(lid, portlet)

        meth_context = self.getMethodContext(datastructure)

        rendered_brains = []
        for brain in self.listItems():
            # layout machinery wants a data structure
            row_dm = BrainDataModel(brain)
            row_ds = DataStructure(datamodel=row_dm)

            row_layout.prepareLayoutWidgets(row_ds) # fill data structure
            rendered = fti._renderLayouts(layout_structures,
                                          row_ds,
                                          context=meth_context,
                                          layout_mode=mode,
                                          )
            rendered_brains.append(rendered)
        return '\n'.join(rendered_brains)


widgetRegistry.register(TabularPortletWidget)
