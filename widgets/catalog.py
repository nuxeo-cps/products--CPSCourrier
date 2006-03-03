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


""" Catalog Tabular Widgets. """

from zLOG import LOG, DEBUG
from Globals import InitializeClass
from AccessControl import Unauthorized

from Products.CMFCore.utils import _checkPermission, getToolByName
from Products.CMFCore.permissions import View, ListFolderContents

from Products.CPSSchemas.Widget import CPSWidget
from Products.CPSSchemas.Widget import widgetRegistry
from Products.CPSSchemas.DataModel import DataModel
from Products.CPSSchemas.DataStructure import DataStructure
from Products.CPSSchemas.BasicWidgets import renderHtmlTag

from Products.CPSCourrier.braindatamodel import BrainDataModel
from Products.CPSCourrier.widgets.tabular import TabularWidget


class CatalogTabularWidget(TabularWidget):
    """ A tabular portlet widget that performs a catalog query.

    Key, values from datastructure starting from FILTER_PREFIX are forwarded
    to the catalog, after stripping the prefix.

    >>> CatalogTabularWidget('the id')
    <CatalogTabularWidget at the_id>
    """

    meta_type = 'Catalog Tabular Widget'

    render_method = 'widget_folder_contents'

    _properties = TabularWidget._properties + (
        {'id': 'fulltext_key', 'type': 'string', 'mode': 'w',
         'label': 'Catalog key for fulltext searchs'},
        {'id': 'fulltext_or', 'type': 'string', 'mode': 'w',
         'label': 'Input filter used for fulltext OR',},
        )

    fulltext_key = ''
    fulltext_or = ''

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

    def filtersToQuery(self, filters):
        """Updates dict to build a query from filters.

        Takes care of fulltext issues. """

        if not self.fulltext_or or not self.fulltext_key:
            return

        filter_or = filters.pop(self.fulltext_or).strip()
        tokens = [token.strip() for token in filter_or.split()]
        nb_tok = len(tokens)

        if not(nb_tok):
            return
        elif nb_tok == 1:
            query_or = tokens[0]
        else:
            query_or = '(%s)' % ' OR '.join(tokens)

        filters[self.fulltext_key] = query_or

    def listRowDataStructures(self, datastructure, layout, **kw):
        """Return datastructures filled with search results meta-data
        """

        catalog = getToolByName(self, 'portal_catalog')

        query = self.buildFilters(datastructure)
        self.filtersToQuery(query)

        brains = catalog(**query)
        dms = (BrainDataModel(brain) for brain in brains)
        datastructures = (DataStructure(datamodel=dm) for dm in dms)
        return [self.prepareRowDataStructure(layout, ds)
                for ds in datastructures]

InitializeClass(CatalogTabularWidget)

widgetRegistry.register(CatalogTabularWidget)
