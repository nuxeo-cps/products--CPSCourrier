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
from Products.CPSSchemas.BasicWidgets import CPSSelectWidget

from Products.CPSSchemas.tests.testWidgets import (FakePortal,
                                                   FakeDataStructure,
                                                   FakeDataModel)

# XXX this should be importable from CPSSchemas.Widget
WIDGET_PREFIX = 'widget__'
WIDGET_PREFIX_len = len('widget__')

class FakeRequest:
    def __init__(self, **kw):
        self.form = kw

class CPSSelectFilterWidget(CPSSelectWidget):
    """A widget that prepares datastructure from dm, request and cookie."""

    meta_type = 'Select Filter Widget'

    def prepare(self, datastructure, **kw):
        """ prepare datastructure from datamodel, request and cookie.

        cookie not implemented.

        >>> datastructure = {}
        >>> widget = CPSSelectFilterWidget('the_id')
        >>> widget.REQUEST = FakeRequest(widget__the_id='abc')
        XXX test needs to be finished
        """

        wid = self.getWidgetId()

        # from datamodel
        CPSSelectWidget.prepare(self, datastructure, **kw)

        # from request
        posted = self.REQUEST.form.get(WIDGET_PREFIX + wid)
        if posted is not None:
            datastructure[wid] = posted


InitializeClass(CPSSelectFilterWidget)

widgetRegistry.register(CPSSelectFilterWidget)
