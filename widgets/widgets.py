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
from Products.CPSPortlets.CPSPortletWidget import CPSPortletWidget
try:
    from Products.CPSSchemas.Widget import widgetRegistry
except ImportError: # BBB for CPS 3.3.8
    old_registration = True
    from Products.CPSSchemas.WidgetTypesTool import WidgetTypeRegistry
    from Products.CPSPortlets.CPSPortletWidget import CPSPortletWidgetType
else:
    old_registration = False

columns_registry = { # This will be handled later by a vocabulary
    'type' : {"label": "label_type",
              "sort_by": 1,
              "data": "display_icon",
              "class" : "Icon",
              },
    'title' : {"label": "label_objet",
               "sort_by": 1,
               "data": "title",
               "link": "url",
               "class": "ShortTitle",
               },
    'auteur' : {"label": "Auteur",
                "sort_by": 1,
                "data": "creator_title",
                },
    'expediteur' : {"label": "Expéditeur",
                    "sort_by": 1,
                    "data": "sender",
                    },
    'delai' : {"label": "Délai",
               "sort_by": 1,
               "data": "date_delai",
               }
    }

def addIdToColumnDescr(id, descr):
    """ A helper function.

    >>> column = {'k':'l', 1:2}
    >>> newcol = addIdToColumnDescr('theid', column)
    >>> newcol['id']
    'theid'

    the original dict was kept untouched
    >>> column.get(id) is None

    All other other data is identical:
    >>> del newcol['id']
    >>> newcol == column
    True

    We don't allow collisions:
    >>> newcol = addIdToColumnDescr('theid', {'id': 'previousid'})
    Traceback (most recent call last):
    ...
    ValueError: Original dict already has an 'id' key
    """

    if descr.has_key('id'):
        raise ValueError("Original dict already has an 'id' key")
    new = descr.copy() # deepcopy overkill here
    new['id'] = id
    return new
    
# This isn't used: just a reference of parameters that didn't go to schema
board_courrier = { 
    "id_tab": "board_courrier",   # replaced by portlet's id
    'categories': ('dashboard',), # replaced by portlet's portal_type
    'query' : {
        'tab': 'courriers_documents', 
        },
}

board_personal = deepcopy(board_courrier)
board_personal['type'] = "MSGSearchBoard" # replaced by widget type
board_personal['query'] = {
    'folder_prefix': 'workspaces/courriers',
    'portal_type': ['incoming_mail',
                    'outgoing_mail',
                    'spontaneous_mail',
                    ],
    'sort-on' : [('modificationdate', 'descending'),],
    }


class DashboardPortletWidget(CPSPortletWidget):
    """ A base widget for tabular rendering of looked up content. """


    render_method = 'msg_searchboard'
    meta_type = 'Dashboard Portlet Widget'
    vocabulary = 'display_columns'

    _properties = CPSPortletWidget._properties + (
        {'id': 'vocabulary', 'type': 'string', 'mode': 'w',
         'label': 'Vocabulary', 'is_required' : 1},
        )


    def getItems(self, datastructure, context):
        """ Method that does the content lookup.

        the context parameter is the context from where the portlet is called.
        If the portlet is rendered through a CPSSkins Portal Group Box Templet,
        that would be the bottom most folder above the request's context.
        """

        raise NotImplementedError

    def getDisplayParams(self, datastructure):
        """ Computes display params from datastructure. """

        context = datastructure.getDataModel().getContext()
        vtool = getToolByName(self, 'portal_vocabularies')
        vocabulary = vtool.getVocabularyFor(context, self.vocabulary)

        params = {}
        params['detail_tab_columns'] = [
            addIdToColumnDescr(col_id, vocabulary.get(col_id))
            for col_id in datastructure.get('columns')
            ]

        # translations for compat. To be dropped later. 
        params['sort_by'] = datastructure['sort_by']
        params['direction'] = datastructure['sort_direction']
        params['nocheckbox'] = datastructure['display_checkbox'] 
        params['items_per_page'] = datastructure['items_per_page']

        return params

    def render(self, mode, datastructure, **kw):
        """ render in mode from datastructure. """
        meth = getattr(self, self.render_method, None)
        if meth is None:
            msg = "Unknown Render Method %s for widget type %s. " \
            + "Please set or change the 'render_method' attribute on " \
            + "your widget declaration."
            raise RuntimeError(msg % (self.render_method, self.getId()))

        context = kw['context_obj']

        # items instead of list_items triggers 
        # nasty side-effects in templates like folder_contents.
        return meth(mode=mode,
                    displayparams=self.getDisplayParams(datastructure),
                    list_items=self.getItems(datastructure, context),
                    datastructure=datastructure,
                    proxy=context,
                    **kw)

class SearchBoardPortletWidget(DashboardPortletWidget):
    """ A dashboard widget based on a search query. """


    render_method = 'msg_searchboard'
    meta_type = 'Search Board Portlet Widget'

    def getItems(self, datastructure, context):
        """ Tries to be iso-functional with msgboards.MSGSearchBoard
        """

        query = {}
        query['folder_prefix'] = datastructure.get('search_context', '')
        query['portal_type'] = datastructure.get('searchable_types', [])
        sort_by = datastructure.get('sort_by')
        sort_direction = datastructure.get('sort_direction')
        if query:
            sort_on = query.get('sort-on', [])
            sort_on.insert(0, (sort_by, sort_direction))

            #query['sort-on'] = sort_on
            if query.get('sort-on'):
                del query['sort-on']

        res = context.search(query)
        return res


class ContentsBoardPortletWidget(DashboardPortletWidget):
    """ A dashboard widget based on a flat folder contents.

    Replacement for msgboards.MSGContentBoard (quoting)
        If kw argument root_rpath is not set, we display content of the object
    rendering the board. If root_rpath is set, we display the content of the
    object found with relative rpath (relative to portal). If kw argument
    relative_to_object is set to one, the root_rpath is considered relative to
    the object rendering the board.

    The equivalent of not setting the kw argument would be not to have a field
    or to set its default value to None
    """

    render_method = 'msg_content_board'
    meta_type = 'Contents Board Portlet Widget'

    def getItems(self, datastructure, context):

        displayed = datastructure.get('searchable_types', [])
        sort_by = datastructure.get('sort_by')
        sort_direction = datastructure.get('sort_direction')
        search_from = datastructure.get('search_context')
        contextual = datastructure.get('contextual')
        # TODO use same name as in content portlet

        if search_from is None: 
            container = context
        elif contextual:
            container = context.restrictedTraverse(search_from)
        else:
            utool = getToolByName(context, 'portal_url')
            portal = utool.getPortalObject()
            ### XXX check that this is enough to ensure security
            container = portal.restrictedTraverse(search_from)

        return container.getFolderContents(displayed=displayed,
                                           sort_by=sort_by,
                                           direction=sort_direction)

InitializeClass(ContentsBoardPortletWidget)

#    One could also think of a widget calling a portal_group_box, hence
#    benefiting from CPSSkins style editor
class RenderedPortletWidget(CPSWidget):
    """ A widget that can render one or several portlets.

    The lookup can made on the slot, the portlet's portal_type, its id.
    It will receive the rendered portlets
    in options/portlets. As usual a non existing slot corresponds to the
    cpsportlets tool.

    If any of those properties is empty, it tries to find it in the
    datastructure

    There is also an optional render_method property

    """

    _properties = CPSWidget._properties + (
        {'id': 'slot', 'type': 'string', 'mode': 'w',
         'label': 'Slot to look in'},
        {'id': 'portlet_id', 'type': 'string', 'mode': 'w',
         'label': 'Portlet id to look for'},
        {'id': 'portlet_types', 'type': 'lines', 'mode': 'w',
         'label': 'Restrict to portlets with a given portal_type'},
        {'id': 'render_method', 'type': 'string', 'mode': 'w',
         'label': 'Rendering method to wrap the rendered portlets'}
        )

    slot = ''
    portlet_id = ''
    portlet_types = []
    render_method = ''

    def getPortlets(self, datastructure, context):
        """ Return the portlets to render. """

        slot = self.slot or datastructure.get(slot)
        portlet_id = self.portlet_id or datastructure.get('portlet_id')
        portlet_types = self.portlet_types or datastructure.get(
            'portlet_types')

        ptltool = getToolByName(self, 'portal_cpsportlets')
        if slot is None:
            context = ptltool
        portlets = ptltool.getPortlets(context=context, slot=slot)

        if portlet_id:
            portlets = [portlet for portlet in portlets
                        if portlet.getId() == portlet_id]
        if portlet_types:
            portlets = [portlet for portlet in portlets
                        if portlet.portal_type in portlet_types]
        ### XXX should protect against the rendering of document portlets!

        return portlets
            
    def prepare(self, datastructure, **kw):
        """Prepare datastructure from datamodel."""
        datastructure[self.getWidgetId()] = None

    def validate(self, datastructure, **kw):
        """Validate datastructure and update datamodel."""

        return True

    def render(self, mode, datastructure, **kw):
        """ Renders from datastructure, in view mode only """

        if mode != 'view':
            return ''

        # finds context
        dm = datastructure.getDataModel()
        context = dm.getProxy()
        if context is None:
            context = dm.getObject()
            
        portlets = self.getPortlets(datastructure, context)
        rendered = [portlet.render(layout_mode=mode, context_obj=context)
                    for portlet in portlets]

        if self.render_method:
            meth = None
        else:
            meth = getattr(self, self.render_method, None)
        if meth is None:
            return '\n'.join(rendered)

        return meth(portlets=rendered, **kw)
    

if old_registration: ### BBB for CPS 3.3.8
    class SearchBoardPortletWidgetType(CPSPortletWidgetType):
        """ Widget Type
        """
        meta_type = 'Search Board Portlet Widget Type'
        cls = SearchBoardPortletWidget

    InitializeClass(SearchBoardPortletWidgetType)

    WidgetTypeRegistry.register(SearchBoardPortletWidgetType,
                                    SearchBoardPortletWidget)


    class ContentsBoardPortletWidgetType(CPSPortletWidgetType):
        """ Widget Type
        """
        meta_type = 'Contents Board Portlet Widget Type'
        cls = ContentsBoardPortletWidget
 
    InitializeClass(ContentsBoardPortletWidgetType)
 
    WidgetTypeRegistry.register(ContentsBoardPortletWidgetType,
                                    ContentsBoardPortletWidget)


    class RenderedPortletWidgetType(CPSPortletWidgetType):
        """ Widget Type
        """
        meta_type = 'Rendered Portlet Widget Type'
        cls = RenderedPortletWidget

    InitializeClass(RenderedPortletWidgetType)

    WidgetTypeRegistry.register(RenderedPortletWidgetType,
                                    RenderedPortletWidget)
else:
    widgetRegistry.register(SearchBoardPortletWidget)    
    widgetRegistry.register(ContentsBoardPortletWidget)    
    widgetRegistry.register(RenderedPortletWidget)    

