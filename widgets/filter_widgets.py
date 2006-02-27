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
            read = c_filters.get(wid)
        except AttributeError: # not a dict
            return

        if isinstance(read, unicode):  # minjson makes all strings unicode
            read = read.encode('iso-8859.15')

        return read

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
    """A select widget that prepares from request and cookies.

    Problem fixed by ugly hack: catalog would want a singleton instead of
    a string and multiselect inappropriate.
    """

    meta_type = 'Select Filter Widget'
    _properties = (CPSSelectWidget._properties
                   + RequestCookiesMixin._properties
                   + ({'id': 'defines_scope', 'type': 'boolean', 'mode': 'w',
 'label': "Is the union of all values is more restrictive than no filtering?"},)
                   )

    defines_scope = False

    def getScope(self, datastructure):
        """return a total scope that might not be equivalent for query
        engines than dropping the value.

        Use-case for this oddity:
        voc of locally accepted portal_types.
        '' is used at position 0 to mean 'all',
        but the query maker will use the list of all existing portal_types
        and datastructure cannot hold lists, because of type inconsistency.

        #XXX TODO factorize in mixin class
        """

        items = self._getVocabulary(datastructure).keys()
        if not items[0]: # raise on empty voc (good thing)
            return list(items[1:]) # see use-case in docstring
        else:
            return list(items)


    def prepare(self, ds, **kw):
        """Prepare datastructure from datamodel."""
        CPSSelectWidget.prepare(self, ds, **kw)
        RequestCookiesMixin.prepare(self, ds, **kw)
        wid = self.getWidgetId()
        if self.defines_scope and not ds[wid]:
            ds[wid+'_scope'] = self.getScope(ds)

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

TOKEN_SUFFIX = '_token'

class CPSToggableCriterionWidget(RequestCookiesMixin, CPSWidget):
    """A widget that manipulates a decorated criterion.

    typical use-case: key to sort on and sort direction. In this use-case, one
    might use the <wid><ref_suffix> to indicate the name of the column (might
    differ from the sort-on key.
    """

    meta_type = 'Toggable Criterion Widget'

    _properties = CPSWidget._properties + RequestCookiesMixin._properties + (
        {'id': 'toggle_tokens', 'type': 'tokens', 'mode': 'w',
         'label': 'Tokens to toggle'}, # we could use a vocabulary, too
        {'id': 'criterion_suffix', 'type': 'string', 'mode': 'w',
         'label': 'Suffix for the criterion'},
        {'id': 'token_suffix', 'type': 'string', 'mode': 'w',
         'label': 'Suffix for the token'},
        {'id': 'ref_suffix', 'type': 'string', 'mode': 'w',
         'label': 'Suffix for a further associated reference'},
        )

    def validate(self, ds, **kw):
        return 1

    def prepare(self, ds, **kw):
        """prepare datastructure from datamodel, request and cookie. """

        wid = self.getWidgetId()
        crit_key = wid + self.criterion_suffix
        token_key = wid + self.token_suffix
        ref_key = wid + self.ref_suffix

        keys = (crit_key, token_key, ref_key)

        dm = ds.getDataModel()

        for key, field in zip(keys, self.fields):
            # from datamodel
            ds[key] = dm[field]

            # from cookie
            from_cookie = self.readCookie(key)
            if from_cookie is not None:
                ds[key] = from_cookie


        # from request form: criterion
        posted = self.REQUEST.form.get(WIDGET_PREFIX + crit_key)

        # do toggle token
        LOG('ToggleWidget.prepare; posted=', DEBUG, posted)
        if posted is not None:
            if posted != ds[crit_key]:
                ds[crit_key] = posted
                ds[token_key] = self.toggle_tokens[0]
            else:
                i = list(self.toggle_tokens).index(ds[token_key])
                order = len(self.toggle_tokens)
                ds[token_key] = self.toggle_tokens[(i+1) % order]

        # from request: ref
        posted = self.REQUEST.form.get(WIDGET_PREFIX + ref_key)
        if posted is not None:
            ds[ref_key] = posted
        LOG('ToggeWidget.prepare, ref:', DEBUG, ds.get(ref_key))
        LOG('ToggeWidget.prepare, crit:', DEBUG, ds.get(crit_key))
        LOG('ToggeWidget.prepare, token:', DEBUG, ds.get(token_key))


    def render(self, mode, datastructure, **kw):
        """ render in mode from datastructure.

        This is used for test/debug purposes only, currently. """

        wid = self.getWidgetId()
        crit_key = wid + self.criterion_suffix
        token_key = wid + self.token_suffix

        crit = datastructure[wid]
        token = datastructure[token_key]
        return '<div>%s, %s</div>' % (crit, token)


InitializeClass(CPSToggableCriterionWidget)

widgetRegistry.register(CPSToggableCriterionWidget)

class CPSPathWidget(CPSWidget):
    """ This widget is a quick & dirty convenience."""

    meta_type = 'Path Widget'

    def prepare(self, datastructure, **kw):
        proxy = (kw.get('context_obj', False)
                 or datastructure.getDataModel().getProxy())
        utool = getToolByName(proxy, 'portal_url')

        # taken from search.py
        portal_path = utool.getPhysicalPath()[1]
        datastructure[self.getWidgetId()] = '/%s/%s' % (portal_path,
                                                        utool.getRpath(proxy),
                                                        )

    def validate(self, datastructure, **kw):
        return 1

    def render(self, mode, datastructure, **kw):
        return ''


InitializeClass(CPSPathWidget)

widgetRegistry.register(CPSPathWidget)
