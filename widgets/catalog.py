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

import logging

from Globals import InitializeClass
from AccessControl import Unauthorized
from ZODB.loglevels import TRACE as TRACE

from Products.CMFCore.utils import _checkPermission, getToolByName
from Products.CMFCore.permissions import View, ListFolderContents

from Products.CPSSchemas.Widget import CPSWidget
from Products.CPSSchemas.Widget import widgetRegistry
from Products.CPSSchemas.DataModel import DataModel
from Products.CPSSchemas.DataStructure import DataStructure
from Products.CPSSchemas.BasicWidgets import renderHtmlTag

from Products.CPSCourrier.braindatamodel import BrainDataModel
from Products.CPSCourrier.widgets.tabular import TabularWidget
from Products.CPSCourrier.config import RANGE_SUFFIX


logger = logging.getLogger('CPSCourrier.widgets.catalog')

class CatalogTabularWidget(TabularWidget):
    """ A tabular portlet widget that performs a catalog query.

    Uses the inherited reading of filter params from datastructure and
    does further work to build the query out of them in the filterToQuery
    method.

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

    fulltext_key = 'SearchableText'
    fulltext_or = 'ZCText_or'

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

        if self.fulltext_or and self.fulltext_key:
            filter_or = filters.pop(self.fulltext_or, '').strip()
            tokens = [token.strip() for token in filter_or.split()]
            nb_tok = len(tokens)

            if nb_tok == 1:
                query_or = tokens[0]
            else:
                query_or = '(%s)' % ' OR '.join(tokens)

            if nb_tok:
                filters[self.fulltext_key] = query_or

        #Ranges
        to_del = []
        for key in filters:
            key_rg = key + RANGE_SUFFIX
            range_ = filters.get(key_rg)
            if range_ is not None:
                to_del.append(key_rg)
                filters[key] = {'query': filters[key],
                                'range' : range_}
        for key in to_del:
            del filters[key]

    def _doBatchedQuery(self, catalog, b_start, b_size, query):
        """ Return batched results, total number of results.

        query will be changed to what was actually sent to the catalog."""

        brains = catalog(**query)
        return brains[b_start:b_start+b_size], len(brains)

    def listRowDataStructures(self, datastructure, layout, **kw):
        """Return datastructures holding search results meta-data & batch info.
        """

        catalog = getToolByName(self, 'portal_catalog')

        query = self.buildFilters(datastructure)
        self.filtersToQuery(query)
        (b_page, b_start, b_size) = self.filtersToBatchParams(query)

        logger.log(TRACE, query)
        brains, nb_results = self._doBatchedQuery(catalog,
                                                  b_start, b_size, query)

        nb_pages = self.getNbPages(nb_results)
        logger.debug("CatalogTabularWidget: "
                     "%d results, %d pages (current %d)" % (nb_results,
                                                            nb_pages,
                                                            b_page))

        dms = (BrainDataModel(brain) for brain in brains)
        datastructures = (DataStructure(datamodel=dm) for dm in dms)
        return ([self.prepareRowDataStructure(layout, ds)
                 for ds in datastructures], b_page, nb_pages)

InitializeClass(CatalogTabularWidget)

widgetRegistry.register(CatalogTabularWidget)


class LuceneTabularWidget(CatalogTabularWidget):

    meta_type = 'Lucene Tabular Widget'

    def _doBatchedQuery(self, catalog, b_start, b_size, query):
        """ Return batched results, total number of results.

        query will be changed to what wbas actually sent to the catalog."""

        query['b_start'] = b_start
        query['b_size'] = b_size

        brains = catalog(**query)
        if brains:
            return brains, brains[0].out_of
        else:
            return [], 0

InitializeClass(LuceneTabularWidget)

widgetRegistry.register(LuceneTabularWidget)
