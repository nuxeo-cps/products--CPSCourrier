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

from urllib import quote

from zLOG import LOG, DEBUG
from Globals import InitializeClass

from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.Widget import CPSWidget
from Products.CPSSchemas.Widget import widgetRegistry
from Products.CPSSchemas.DataStructure import DataStructure

from Products.CPSPortlets.CPSPortletWidget import CPSPortletWidget

WIDGET_PREFIX = 'widget__'

class TabularWidget(CPSPortletWidget):
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

    >>> wi = TabularWidget('spam')
    """

    _properties = _properties = CPSPortletWidget._properties + (
        {'id': 'row_layout', 'type': 'string', 'mode': 'w',
         'label': 'Layout to use for the rows', 'is_required' : 1},
        {'id': 'empty_message', 'type': 'string', 'mode': 'w',
         'label': 'Message to display if listing is empty',},
        {'id': 'is_empty_message_i18n', 'type': 'boolean', 'mode': 'w',
         'label': 'Is the message of emptiness to be translated?'},
        {'id': 'actions_category', 'type': 'string', 'mode': 'w',
         'label': 'Actions category for buttons'},
        )

    row_layout = ''
    render_method = ''
    empty_message = ''
    is_empty_message_i18n = False
    actions_category = ''
    actions = ()

    def prepareRowDataStructure(self, layout, datastructure):
        """Have layout prepare row datastructure and return it."""
        layout.prepareLayoutWidgets(datastructure)
        return datastructure

    def listRowDataStructures(self, datastructure, layout, **kw):
        """Return items datastructures, prepared by layout

        It's probably a good idea to return an iterator.
        """
        raise NotImplementedError

    def getCallingObject(self, datastructure):
        """Get the object for which this widget is called.

        Typically a portlet."""

        dm = datastructure.getDataModel()
        proxy = dm.getProxy()
        if proxy is None:
            return dm.getObject()
        else:
            return proxy

    def getMethodContext(self, datastructure):
        """Return the context from where to lookup the layout rendering method.

        Override this if you want to replace a slow zpt parsing by fixed python
        code.

        To do this for widgets would require to pass the context at
        datamodel init time or hack it afterwards.
        This could be dangerous because of ACL checks and local roles.
        """

        return datastructure.getDataModel().getContext()

    def columnFromWidget(self, widget, datastructure,
                         sort_wid='Query sort'):
        """ make column info from a widget object.

        Return (widget, boolean, token, get_req) where:
        - boolean tells whether this column is used as sorting reference
        - token is the associated token (e.g, 'ascending' etc)
        - get_req is the get part of the url to toggle sort.
        XXX might break with flexible layouts because it relies on the column
        id.
        XXX might be a good idea to make a property out of 'sort_widget'
        XXX this currently uses -col,-token and -on suffixes to exchange info
        with
        a toggable widget of the current object (we have a corresponding
        datastructure but cannot have this widget in itself).
        Make these strings default values of props on the tabular
        widget (an sort widget also) for flexibility and and tight default
        config
        """

        sortable = getattr(widget, 'sortable', None)
        if not sortable:
            return (widget, False, '', '')

        # prepare the get request
        wid = widget.getWidgetId()
        prefixed = WIDGET_PREFIX + sort_wid
        get_req = '?%s-on=%s&%s-col=%s&%s=go' % (prefixed,
                                           quote(sortable),
                                           prefixed,
                                           wid,
                                           self.filter_button,
                                           )

        sort_col = datastructure.get(sort_wid+'-col') # make -col a prop
        if sort_col != wid:
            return (widget, False, '', get_req)

        # this column is the sorting reference.
        token = datastructure.get(sort_wid+'-order') # make -order a prop
        return (widget, True, token, get_req)

    def extractColumns(self, datastructure, layout_structure):
        """ Extract column info for render method from a layout structure. """

        return [ self.columnFromWidget(row[0]['widget'], datastructure)
                 for row in layout_structure['rows'] ]

    def getActions(self, datastructure):
        if not self.actions_category:
            return None

        atool = getToolByName(self, 'portal_actions')

        proxy = datastructure.get('context_obj') # if from portlet
        if proxy is None:
            proxy = datastructure.getDataModel().getProxy()

        cat = self.actions_category or 'object'
        actions = atool.listFilteredActionsFor(proxy)[self.actions_category]
        return [{'title': action['name'],
                'url': action['url'],
                 'id' : action['id'],}
                for action in actions]

    def render(self, mode, datastructure, **kw):
        """ Render datastructure according to mode.

        Rows layout structures are computed once and for all, on the first
        object to display.
        """
        calling_obj = self.getCallingObject(datastructure)
        if calling_obj is None: # happens on creation
            return ''

        # GR tired of this duplication. refactor after tests are written
        proxy = datastructure.get('context_obj') # if from portlet
        if proxy is None:
            proxy = datastructure.getDataModel().getProxy()


        # lookup of row layout
        lid = self.row_layout
        fti = calling_obj.getTypeInfo()
        row_layout = fti.getLayout(lid, calling_obj)
        layout_structures = None

        meth_context = self.getMethodContext(datastructure)

        rendered_rows = []
        for row_ds in self.listRowDataStructures(datastructure,
                                                 row_layout, **kw):
            # compute layout_structures if needed
            if layout_structures is None:
                row_dm = row_ds.getDataModel()
                layout_structures = [
                    row_layout.computeLayoutStructure(mode, row_dm)]

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

        if layout_structures is None: # listing is empty
            msg = self.empty_message
            cpsmcat = getToolByName(self, 'translation_service')
            if self.is_empty_message_i18n:
                msg = cpsmcat(msg)
            if isinstance(msg, unicode):
                msg = msg.encode('iso-8859-15')
            return msg

        layout_structure = layout_structures[0] # only one layout
        columns = self.extractColumns(datastructure, layout_structure)
        actions = self.getActions(datastructure)

        return meth(mode=mode, columns=columns,
                    rows=rendered_rows, actions=actions,
                    here_url=proxy.absolute_url())


widgetRegistry.register(TabularWidget)
