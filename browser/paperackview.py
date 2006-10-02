# Copyright (c) 2006 Nuxeo SAS <http://nuxeo.com>
# Authors: Georges Racinet <gracinet@nuxeo.com>
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

import logging

from Products.Five.browser import BrowserView

from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.Widget import widgetname
from Products.CPSSchemas.BasicWidgets import renderHtmlTag
from Products.CPSDashboards.utils import unserializeFromCookie

logger = logging.getLogger('CPSCourrier.browser.paperackview')

class PaperAckView(BrowserView):
    """This class provide views to prepare acknowledgements to be printed
    or sent by email.

    It relies on the following assumptions:
    - The content widget's is standard, or at least :
        - its getWidgetModeFromLayoutMode() reacts to prefixes
        - its getHtmlWidgetId is the standard one.
    """

    layout_id = 'pmail_ack'
    content_wid = 'content'
    flag_field = 'flag_ack'
    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        self.html_wid = widgetname(self.content_wid)

    def renderPrepare(self):
        """render the layout with prefilled info in the content text widget."""
        doc = getattr(self, 'doc', None)
        if doc is None:
            self.doc = self.context.getContent()
        html_wid = widgetname(self.content_wid)
        self.request.form.update({html_wid: self.prefill()})
        return self.doc.render(layout_mode='edit',
                               layout_id=self.layout_id,
                               proxy=self.context,
                               request=self.request)

    def renderPrint(self):
        """render the layout with posted info, in view_print mode.

        We use the layout mode to exclude other widgets than content
        """
        self.flagAcked()
        return self.doc.validateStoreRender(layout_mode_err='edit',
                                            layout_mode_ok='view_print',
                                            cluster=self.cluster,
                                            proxy=self.context,
                                            )

    def emailAck(self, printable=False):
        """send the ack via email with posted info.

        Optionally render print page again.
        """
        raise NotImplementedError

    def prefill(self):
        """Compute prefilled data."""
        doc = getattr(self, 'doc', None)
        if doc is None:
            doc = self.doc = self.context.getContent()
        # To complete
        return '<h3> This is the prefilled content </h3>'


    def flagAcked(self):
        """flag the doc as acked.

        Store doc on self to avoid yet another getContent, even from cache."""

        doc = self.context.getEditableContent()
        doc.edit(mapping={self.flag_field:True})
        self.doc = doc
