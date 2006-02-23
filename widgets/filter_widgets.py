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
from zLOG import LOG, DEBUG
from Globals import InitializeClass

from Products.CMFCore.utils import getToolByName
from Products.CPSSchemas.Widget import CPSWidget
from Products.CPSSchemas.Widget import widgetRegistry
from Products.CPSSchemas.BasicWidgets import renderHtmlTag
from Products.CPSSchemas.BasicWidgets import (CPSSelectWidget,
                                              CPSMultiSelectWidget)
from Products.CPSSkins.cpsskins_utils import unserializeFromCookie

from Products.CPSSchemas.tests.testWidgets import (FakePortal,
                                                   FakeDataStructure,
                                                   FakeDataModel)


# XXX this should be importable from CPSSchemas.Widget
WIDGET_PREFIX = 'widget__'
WIDGET_PREFIX_len = len('widget__')

class FakeRequest:
    def __init__(self, **kw):
        self.form = kw

class RequestCookiesMixin:
    """prepare datastructure from dm, request and cookie."""

    _properties = (
        {'id': 'cookie_id', 'type': 'string', 'mode': 'w',
         'label': 'Name of cookie for filter params (no cookie if empty)', },
        )

    cookie_id = ''

    def readCookie(self, wid):
        """Read a value for datastructure from cookie.

        XXX should go in a mixin class
        """
        if not self.cookie_id:
            return
        cookie = self.REQUEST.cookies.get(self.cookie_id)
        if cookie is None:
            return

        # we have to convert from unicode. There should be only identifiers
        # so we don't catch UnicodeEncodeErrors
        c_filters = unserializeFromCookie(string=cookie)
        LOG('CPSSelectFilterWidget:cookie', DEBUG, c_filters)
        LOG('CPSSelectFilterWidget:wid', DEBUG, wid)
        try:
            return str(c_filters.get(wid))
        except (AttributeError, KeyError):
            pass


    def prepare(self, datastructure, **kw):
        """ prepare datastructure from datamodel, request and cookie.

        cookie not implemented.

        >>> datastructure = {}
        >>> widget = CPSSelectFilterWidget('the_id')
        >>> widget.REQUEST = FakeRequest(widget__the_id='abc')
        XXX test needs to be finished
        """

        wid = self.getWidgetId()

        # from datamodel already done in subclass

        # from cookie
        from_cookie = self.readCookie(wid)
        if from_cookie is not None:
            datastructure[wid] = from_cookie

        # from request form
        posted = self.REQUEST.form.get(WIDGET_PREFIX + wid)
        if posted is not None:
            datastructure[wid] = posted

#
# Widgets
#

class CPSSelectFilterWidget(RequestCookiesMixin, CPSSelectWidget):
    """A multiselect widget that prepares from request and cookies. """

    meta_type = 'Select Filter Widget'
    _properties = CPSSelectWidget._properties + RequestCookiesMixin._properties

    def prepare(self, ds, **kw):
        CPSSelectWidget.prepare(self, ds, **kw)
        RequestCookiesMixin.prepare(self, ds, **kw)

InitializeClass(CPSSelectFilterWidget)

widgetRegistry.register(CPSSelectFilterWidget)


class CPSMultiSelectFilterWidget(RequestCookiesMixin, CPSMultiSelectWidget):
    """A multiselect widget that prepares from request and cookies. """

    meta_type = 'MultiSelect Filter Widget'
    _properties = CPSMultiSelectWidget._properties + RequestCookiesMixin._properties

    def prepare(self, ds, **kw):
        CPSMultiSelectWidget.prepare(self, ds, **kw)
        RequestCookiesMixin.prepare(self, ds, **kw)


InitializeClass(CPSMultiSelectFilterWidget)

widgetRegistry.register(CPSMultiSelectFilterWidget)
