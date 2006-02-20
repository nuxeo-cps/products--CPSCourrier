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
from Globals import InitializeClass

from Products.CMFCore.utils import getToolByName
from Products.CPSSchemas.Widget import CPSWidget
from Products.CPSSchemas.Widget import widgetRegistry

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
        else:
            icon = obj.getIcon(relative_to_portal=1)
            ptype = obj.portal_type

            # XXX this should be factorized among widgets (at the very least)
            utool = getToolByName(self, 'portal_url')
            base_url = utool.getBaseUrl()
            
            return context.getImgTag(icon,
                                     base_url=base_url, title=ptype)

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
        """Prepare datastructure from datamodel."""
        pass
            
    def validate(self, datastructure, **kw):
        """Validate datastructure and update datamodel."""
        return 1

    def render(self, mode, datastructure, **kw):
        """Render in mode from datastructure."""

        dm = datastructure.getDataModel()
        proxy = dm.getProxy()
        if proxy is None:
            return ''
        wftool = getToolByName(self, 'portal_workflow')
        # TODO translate
        return wftool.getInfoFor(proxy, 'wf_var_id')

InitializeClass(CPSWorkflowVariableWidget)

widgetRegistry.register(CPSWorkflowVariableWidget)

