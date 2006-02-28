# Copyright (c) 2006 Nuxeo SAS <http://nuxeo.com>
# Author : Georges Racinet <gracinet@nuxeo.com>
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

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.Widget import CPSWidget, widgetRegistry
from Products.CPSWorkflow.stack import Stack

class CPSStackWidget(CPSWidget):
    """ A widget that wraps a stack rendering. """

    meta_type = "Workflow Stack Widget"

    security = ClassSecurityInfo()

    _properties = CPSWidget._properties + (
        {'id': 'stack_var_id', 'type': 'string', 'mode': 'w',
         'label': 'Workflow variable holding the stack'},
        )

    fields = []

    security.declarePrivate('getContext')
    def getContext(self, datastructure):
        """Obtain the proxy or cps document for which this widget works.

        No security declaration, same as Widget._createExpressionContext
        XXX GR Such a lightweight method doesn't seem to be part of the base
        class API. Probably should.
        """

        dm = datastructure.getDataModel()
        context = dm.getProxy()
        if context is None:
            context = dm.getObject()

        return context


    def prepare(self, datastructure, **kw):
        """Prepare datastructure from datamodel."""
        datamodel = datastructure.getDataModel()
        if len(self.fields):
            datastructure[self.getWidgetId()] = datamodel[self.fields[0]]
        else:
            datastructure[self.getWidgetId()] = None

    def validate(self, datastructure, **kw):
        """Validate datastructure and update datamodel."""
        widget_id = self.getWidgetId()
        err = 0
        v = datastructure[widget_id]
        if err:
            datastructure.setError(widget_id, err)
            datastructure[widget_id] = v
        else:
            datamodel = datastructure.getDataModel()
            if len(self.fields):
                datamodel[self.fields[0]] = v

        return not err

    def render(self, mode, datastructure, **kw):
        """Render the stack.
        """

        stack_var_id = self.stack_var_id
        wftool = getToolByName(self, 'portal_workflow')

        context = self.getContext(datastructure)
        try:
            stack = wftool.getInfoFor(context, stack_var_id)
        except KeyError, err:
            if str(err) == "'%s'" % stack_var_id:
                raise RuntimeError(
                    "Workflow variable '%s' requested by widget type '%s' not found"
                    % (stack_var_id, self.getId()))
            else:
                raise
        if not isinstance(stack, Stack):
            raise ValueError("Workflow variable %s is not a stack"
                             % stack_var_id)

        return stack.render(context=context, mode=mode, **kw)

InitializeClass(CPSStackWidget)

widgetRegistry.register(CPSStackWidget)
