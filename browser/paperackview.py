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
from urllib import urlencode

from Products.Five.browser import BrowserView

from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.Widget import widgetname
from Products.CPSSchemas.BasicWidgets import renderHtmlTag
from Products.CPSDocument.utils import getFormUidUrlArg
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
    flag_field = 'ack_sent'
    prefill_cluster = 'header'

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        self.html_wid = widgetname(self.content_wid)
        # Would be slightly better to introspect theme page
        self.is_print = bool(request.form.get('pp'))

    def getId(self):
        # useful for portlet guards
        return self.__name__

    def renderLayout(self):
        """render the layout with prefilled info in the content text widget."""
        doc = getattr(self, 'doc', None)
        if doc is None:
            self.doc = self.context.getContent()
        html_wid = widgetname(self.content_wid)

        form = self.request.form
        mode = form.get('mode', 'edit')
        if mode != 'view_print' and not form.get('html_wid'):
            form.update({html_wid: self.prefill()})

        return self.doc.render(layout_mode=mode,
                               layout_id=self.layout_id,
                               proxy=self.context,
                               use_session=mode == 'edit',
                               no_form=True,
                               request=self.request)

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
        return doc.render(cluster=self.prefill_cluster,
                          context=self.context,
                          layout_mode="view_ack",
                          proxy=self.context)

    def flagAcked(self):
        """flag the doc as acked.

        Store doc on self to avoid yet another getContent, even from cache."""

        doc = self.context.getEditableContent()
        doc.edit(mapping={self.flag_field:True})
        self.doc = doc

    def dispatchSubmit(self):
        form = self.request.form
        resp = self.request.RESPONSE
        url = '/'.join((self.context.absolute_url(), self.__name__+'.html'))
        if 'print_ack' in form:
            doc = self.context.getContent()
            valid, ds = doc.validate(layout_id=self.layout_id,
                                     proxy=self.context,
                                     request=self.request,
                                     use_session=True)
            if valid:
                self.flagAcked()
                resp.redirect('%s?pp=1&mode=view_print' % url)
            else:
                psm = 'psm_content_error'
                args = getFormUidUrlArg(REQUEST)
                args['portal_status_message'] = psm
                resp.redirect('%s?%s' % (url, urlencode(args)))

        elif 'email_ack' in form:
            raise NotImplementedError
        else:
            self.request.RESPONSE.redirect(url)
            return ''
