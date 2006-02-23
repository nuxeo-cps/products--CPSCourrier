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

""" This module holds simple widget definitions for CPSCourrier row layouts.
"""
from cgi import escape
from Globals import InitializeClass

from Products.CMFCore.utils import getToolByName
from Products.CPSSchemas.Widget import CPSWidget
from Products.CPSSchemas.Widget import widgetRegistry
from Products.CPSSchemas.BasicWidgets import renderHtmlTag


class CPSTypeIconWidget(CPSWidget):
    """widget showing the icon associated to the object's portal_type. """
    meta_type = 'Type Icon Widget'

    def prepare(self, datastructure, **kw):
        """Prepare datastructure from datamodel."""
        dm = datastructure.getDataModel()
        obj = dm.getObject()
        context = dm.getContext()
        if obj is None or context is None:
            return
        datastructure[self.getWidgetId()] = obj.portal_type

    def validate(self, datastructure, **kw):
        """Validate datastructure and update datamodel."""
        return 1

    def render(self, mode, datastructure, **kw):
        """Render in mode from datastructure."""

        ptype = datastructure.get(self.getWidgetId())
        if ptype is None:
            return ''

        ttool = getToolByName(self, 'portal_types')
        fti = getattr(ttool, ptype)
        icon = fti.getIcon()

        utool = getToolByName(self, 'portal_url')
        uri = utool.getBaseUrl() + icon
        title = fti.title_or_id()
        cpsmcat = getToolByName(self, 'translation_service')
        title = cpsmcat(title).encode('iso-8859-15')
        return renderHtmlTag('img', src=uri, alt=title)


InitializeClass(CPSTypeIconWidget)

widgetRegistry.register(CPSTypeIconWidget)

class CPSWorkflowVariableWidget(CPSWidget):
    """widget showing the value of a workflow_variable.

    By default this is review_state.
    """

    meta_type = 'Workflow Variable Widget'

    _properties = CPSWidget._properties + (
        {'id': 'wf_var_id', 'type' : 'string', 'mode' : 'w',
         'label': 'Name of the workflow variable to pick'},
        )

    wf_var_id = 'review_state'

    def prepare(self, datastructure, **kw):
        """Prepare datastructure from workflow var."""

        dm = datastructure.getDataModel()
        proxy = dm.getProxy()
        if proxy is None:
            return ''
        wftool = getToolByName(self, 'portal_workflow')
        datastructure[self.getWidgetId()] = wftool.getInfoFor(proxy,
                                                              self.wf_var_id)

    def validate(self, datastructure, **kw):
        """Validate datastructure and update datamodel."""
        return 1

    def render(self, mode, datastructure, **kw):
        """Render in mode from datastructure."""

        cpsmcat = getToolByName(self, 'translation_service')
        state = datastructure[self.getWidgetId()]
        return escape(cpsmcat(state).encode('iso-8859-15'))


InitializeClass(CPSWorkflowVariableWidget)

widgetRegistry.register(CPSWorkflowVariableWidget)
class CPSQualifiedLinkWidget(CPSWidget):
    """widget that makes a single <a> tag out of three informations.

    If only two fields are provided they are used as text and optional text.
    If there's a third, it holds the link destination (absolute).
    Otherwise the widget uses the proxy's url.
    """

    meta_type = 'Qualified Link Widget'

    field_types = ('CPS String Field', 'CPS String Field', 'CPS String Field')

    def prepare(self, datastructure, **kw):
        """Prepare datastructure from workflow var."""

        w_id = self.getWidgetId()
        dm = datastructure.getDataModel()

        suffixes = ('contents', 'title', 'href')
        for suffix, fid in zip(suffixes, self.fields):
            datastructure['%s_%s' % (w_id, suffix)] = dm[fid]
        if len(self.fields) < 3: # no url field
            proxy = dm.getProxy()
            if proxy is None:
                raise ValueError(
                    "No field provided for link, no proxy object found")
            utool = getToolByName(self, 'portal_url')
            base_url = utool.getBaseUrl()
            rpath = utool.getRpath(proxy)

            datastructure['%s_%s' % (w_id, 'href')] = base_url+rpath

    def validate(self, datastructure, **kw):
        """Validate datastructure and update datamodel."""
        return 1

    def render(self, mode, datastructure, **kw):
        """Render in mode from datastructure."""

        w_id = self.getWidgetId()
        params = dict((suffix, datastructure['%s_%s' % (w_id, suffix)])
                       for suffix in ('href', 'title', 'contents',))
        return renderHtmlTag('a', **params)


InitializeClass(CPSQualifiedLinkWidget)

widgetRegistry.register(CPSQualifiedLinkWidget)

class CPSListCheckboxWidget(CPSWidget):
    """widget making a checkbox, to be posted as a list.

    This will probably be extended in the future to take complex visibility
    conditions into account.

    If no field provided, try and find the associated proxy's id for the list
    otherwise pick the field value.
    """

    meta_type = 'List Checkbox Widget'

    _properties = CPSWidget._properties + (
        {'id': 'list_name', 'type' : 'string', 'mode' : 'w',
         'label': 'Name of the posted list', 'is_required': 1},
        )

    list_name = ''

    def prepare(self, datastructure, **kw):
        """Prepare datastructure. """

        dm = datastructure.getDataModel()
        if self.fields:
            value = dm[self.fields[0]]
        else:
            proxy = dm.getProxy()
            if proxy is None:
                raise ValueError(
                    "No field, and datamodel is not associated to a proxy")
            value = proxy.getId()
        datastructure[self.getWidgetId()] = value

    def validate(self, datastructure, **kw):
        """Validate datastructure and update datamodel."""
        return 1

    def render(self, mode, datastructure, **kw):
        """Render in mode from datastructure."""

        name = '%s:list' % self.list_name
        value = datastructure[self.getWidgetId()]
        # XXX: content_lib_info_detail_tab uses  item.getContextUrl(utool=utool)
        # investigate ?
        return renderHtmlTag('input', type='checkbox',
                             name=name, value=value)


InitializeClass(CPSListCheckboxWidget)

widgetRegistry.register(CPSListCheckboxWidget)
