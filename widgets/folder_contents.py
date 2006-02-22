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


""" Folder Contents Portlet Widgets. """

from zLOG import LOG, DEBUG
from Globals import InitializeClass
from AccessControl import Unauthorized

from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.permissions import ListFolderContents

from Products.CPSSchemas.Widget import CPSWidget
from Products.CPSSchemas.Widget import widgetRegistry
from Products.CPSSchemas.DataModel import DataModel
from Products.CPSSchemas.DataStructure import DataStructure
from Products.CPSSchemas.BasicWidgets import renderHtmlTag

from Products.CPSCourrier.widgets.tabular import TabularWidget

FILTER_PREFIX = "Filter "
FILTER_PREFIX_LEN = len(FILTER_PREFIX)

def removeFilterPrefix(wid):
    """Remove a filter prefix in a widget id. """

    if wid.startswith(FILTER_PREFIX):
        return wid[FILTER_PREFIX_LEN:]
    else:
        return wid

class FolderContentsWidget(TabularWidget):
    """ A tabular portlet widget that performs a simple folder listing.

    Information is fetched from the folder's objects of a given meta-type.
    There's no batching or sorting.

    >>> FolderContentsWidget('the_id')
    <FolderContentsWidget at the_id>
    """

    meta_type = 'Folder Contents Widget'
    _properties = TabularWidget._properties + (
        {'id': 'listed_meta_types', 'type': 'lines', 'mode': 'w',
         'label': 'Meta types to list', 'is_required' : 1},
        )

    listed_meta_types = (
       'CPS Proxy Document',
       'CPS Proxy Folder',
       'CPS Proxy Folderish Document',
       )

    render_method = 'widget_folder_contents'

    def layout_row_view(self, layout=None, **kw):
        """Render method for rows layouts in 'view' mode.
        """

        if layout is None:
            raise ValueError("Computed layout is None")
        cells = (row[0] for row in layout['rows'])
        tags = (renderHtmlTag('td',
                              css_class=cell.get('widget_css_class'),
                              contents=cell['widget_rendered'],
                              )
                for cell in cells)
        return ''.join(tags)

    def getMethodContext(self, datastructure):
        return self

    def prepareDataStructure(self, layout, datastructure):
        """Get layout to prepare datastructure and return it."""
        layout.prepareLayoutWidgets(datastructure)
        return datastructure

    def listRowDataStructures(self, datastructure, layout, **kw):
        """Return an iterator for folder contents datastructures
        """
        folder = kw.get('context_obj') # typical of portlets
        if folder is None:
            folder = datastructure.getDataModel().getProxy()

        if not _checkPermission(ListFolderContents, folder):
            raise Unauthorized("You are not allowed to list this folder")
        meta_types = datastructure.get('meta_types') or self.listed_meta_types

        iterprox = (folder[p_id] for p_id in folder.objectIds(meta_types))
        iterdocs = ( (proxy.getContent(), proxy) for proxy in iterprox)
        iterdms = (doc.getTypeInfo().getDataModel(doc,
                                                  proxy=proxy, context=folder)
                   for doc, proxy in iterdocs)
        iterds = (self.prepareDataStructure(layout, DataStructure(datamodel=dm))
                  for dm in iterdms)
        return iterds

InitializeClass(FolderContentsWidget)

widgetRegistry.register(FolderContentsWidget)
