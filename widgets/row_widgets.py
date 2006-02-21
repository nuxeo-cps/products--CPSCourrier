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
        pass

    def validate(self, datastructure, **kw):
        """Validate datastructure and update datamodel."""
        return 1

    def render(self, mode, datastructure, **kw):
        """Render in mode from datastructure."""

        dm = datastructure.getDataModel()
        obj = dm.getObject()
        context = dm.getContext()
        if obj is None or context is None:
            return ''

        utool = getToolByName(self, 'portal_url')
        fti = obj.getTypeInfo()
        icon = fti.getIcon()
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
        state = datastructure[self.getWidgetId()])
        return cpsmcat(state).encode('iso-8859-15')


InitializeClass(CPSWorkflowVariableWidget)

widgetRegistry.register(CPSWorkflowVariableWidget)
class CPSQualifiedLinkWidget(CPSWidget):
    """widget that makes a single <a> tag out of three informations.

    If only two fields are provided they serve as text an optional text.
    If there's a third, it holds the link destination (absolute)
    """

    meta_type = 'Qualified Link Widget'

#    _properties = CPSWidget._properties + (
#        {'id': 'wf_var_id', 'type' : 'string', 'mode' : 'w',
#         'label': 'Name of the workflow variable to pick'},
#        )

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
