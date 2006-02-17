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

from zLOG import LOG, DEBUG
from Globals import InitializeClass

from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.Widget import CPSWidget
from Products.CPSSchemas.Widget import widgetRegistry
from Products.CPSSchemas.DataStructure import DataStructure

from Products.CPSPortlets.CPSPortletWidget import CPSPortletWidget

class TabularPortletWidget(CPSPortletWidget):
    """ A generic portlet widget to display tabular contents.

    Uses a layout to render the rows. This layout is fetched from the portlet.
    Subclasses have to override the 'listRowDataModels' method. 

    The (optional) render method will get those keyword args:
    - mode: the widget's rendering mode
    - rows: list of rendered rows
    - columns: the common list of widget objects that were used to render
               rows. 

    We assume that the 'layout' part of the row layout definition is
    actually a column, because that's what flexible widgets manipulation
    methods are comfortable with. It's up to the layout's render method to
    render this column as a row. To get rid of this assumption, subclasses
    can override the extractColumns method. 
    
    >>> wi = TabularPortletWidget('spam')
    """

    meta_type = "Tabular Portlet Widget"

    _properties = _properties = CPSPortletWidget._properties + (
        {'id': 'row_layout', 'type': 'string', 'mode': 'w',
         'label': 'Layout to use for the rows', 'is_required' : 1},
        )

    row_layout = ''
    render_method = ''

    def listRowDataModels(self):
        """To be implemented by subclasses.

        The row_layout layout will work on these.
        It's probably a good idea to return an iterator.
        """
        raise NotImplementedError

    def getPortlet(self, datastructure):
        return datastructure.getDataModel().getObject()

    def getMethodContext(self, datastructure):
        """Return the context from where to lookup the layout rendering method.

        Override this if you want to replace a slow zpt parsing by fixed python
        code.
        
        To do this for widgets would require to pass the context at
        datamodel init time or hack it afterwards. 
        This could be dangerous because of ACL checks and local roles. 
        """
        
        return datastructure.getDataModel().getContext()

    def extractColumns(self, layout_structure):
        """ Extract column info for render method from a layout structure. """

        return [ row[0]['widget'] for row in layout_structure['rows'] ]
    
    def render(self, mode, datastructure, **kw):
        portlet = self.getPortlet(datastructure)

        lid = self.row_layout
        fti = portlet.getTypeInfo()
        layout_structures = fti._computeLayoutStructures(
            datastructure, 'view', layout_id=lid, ob=portlet)
        # maybe can be fetched from the layout structures as well (perf)
        row_layout = fti.getLayout(lid, portlet)

        meth_context = self.getMethodContext(datastructure)

        rendered_rows = []
        for row_dm in self.listRowDataModels():
            # prepare a data structure
            row_ds = DataStructure(datamodel=row_dm)
            row_layout.prepareLayoutWidgets(row_ds)

            # render from row_ds
            rendered = fti._renderLayouts(layout_structures,
                                          row_ds,
                                          context=meth_context,
                                          layout_mode=mode,
                                          )
            rendered_rows.append(rendered)

        if not self.render_method: # default behaviour that can still be useful
            return '\n'.join(rendered_rows)

        meth = getattr(meth_context, self.render_method, None)
        if meth is None:
            raise RuntimeError("Unknown Render Method %s for widget type %s"
                               % (self.render_method, self.getId()))

        layout_structure = layout_structures[0] # only one layout
        columns = self.extractColumns(layout_structure)
        return meth(mode=mode, columns=columns, rows=rendered_rows)


widgetRegistry.register(TabularPortletWidget)
