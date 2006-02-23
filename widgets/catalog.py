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

from Products.CMFCore.utils import _checkPermission, getToolByName
from Products.CMFCore.permissions import View, ListFolderContents

from Products.CPSSchemas.Widget import CPSWidget
from Products.CPSSchemas.Widget import widgetRegistry
from Products.CPSSchemas.DataModel import DataModel
from Products.CPSSchemas.DataStructure import DataStructure
from Products.CPSSchemas.BasicWidgets import renderHtmlTag
from Products.CPSSkins.cpsskins_utils import serializeForCookie

from Products.CPSCourrier.braindatamodel import BrainDataModel
from Products.CPSCourrier.widgets.tabular import TabularWidget


FILTER_PREFIX = 'Query '
FILTER_PREFIX_LEN = len('Query ')
SCOPE_SUFFIX = '_scope' # see explanations in filter_widgets

_missed = object()

def removeFilterPrefix(wid):
    """Remove a filter prefix in a widget id. """

    if wid.startswith(FILTER_PREFIX):
        return wid[FILTER_PREFIX_LEN:]
    else:
        return wid


class CatalogTabularWidget(TabularWidget):
    """ A tabular portlet widget that performs a simple folder listing.

    Information is fetched from the folder's objects of a given meta-type.
    There's no batching or sorting.

    >>> CatalogTabularWidget('the id')
    <CatalogTabularWidget at the_id>
    """

    meta_type = 'Catalog Tabular Widget'
    _properties = TabularWidget._properties + (
        {'id': 'cookie_id', 'type': 'string', 'mode': 'w',
         'label': 'Name of cookie for filter params (no cookie if empty)', },
        {'id': 'filter_button', 'type': 'string', 'mode': 'w',
         'label': 'Name of the button used to trigger filtering', },
        )

    listed_meta_types = (
       'CPS Proxy Document',
       'CPS Proxy Folder',
       'CPS Proxy Folderish Document',
       )

    cookie_id = ''

    filter_button = ''

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

    def buildFilters(self, datastructure):
        """Build query according to datastructure, query and cookies.

        Cookies not implemented.
        Assumptions: the post is made with widgets whose ids start all with
        'Query '
        and correspond to other widget ids present in items.

        XXX TODO this is a cc from folder_contents. Factorize to base class
        """

        # extract filters from datastructure
        prefilt = dict( (key, item)
                       for key, item in datastructure.items()
                       if key.startswith(FILTER_PREFIX)
                       and not key.endswith(SCOPE_SUFFIX))

        # if filtering uses a post, set cookie
        request = self.REQUEST
        if self.cookie_id and request.form.get(self.filter_button):
            cookie = serializeForCookie(prefilt)
            request.RESPONSE.setCookie(self.cookie_id, cookie)

        # replace some empty filters by the corresponding total scope
        # and remove the others
        filters = {}
        for key, item in prefilt.items():
            if item:
                filters[key[FILTER_PREFIX_LEN:]] = item
                continue
            scope = datastructure.get(key + SCOPE_SUFFIX)
            if scope is not None:
                filters[key[FILTER_PREFIX_LEN:]] = scope

        LOG('Catalog Tabular Widget; filters:', DEBUG, filters)
        return filters

    def listRowDataStructures(self, datastructure, layout, **kw):
        """Return datastructures filled with search results meta-data
        """

        catalog = getToolByName(self, 'portal_catalog')

        query = self.buildFilters(datastructure)
        brains = catalog(**query)
        dms = (BrainDataModel(brain) for brain in brains)
        datastructures = (DataStructure(datamodel=dm) for dm in dms)
        return [self.prepareRowDataStructure(layout, ds)
                for ds in datastructures]

InitializeClass(CatalogTabularWidget)

widgetRegistry.register(CatalogTabularWidget)
