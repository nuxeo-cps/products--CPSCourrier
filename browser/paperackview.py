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

from Acquisition import aq_inner, aq_parent
from Products.Five.browser import BrowserView

from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.Widget import widgetname
from Products.CPSSchemas.DataStructure import DataStructure
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

    Calls the prefill cluster on current doc and (directly)
    two widgets from 'parent_layout' on parent to render the prefilled content.
    This is a bit low level, but two layouts was not satisfactory either
    (too heavy)
    """

    layout_id = 'pmail_ack'
    content_wid = 'content'
    flag_field = 'ack_sent'
    prefill_cluster = 'header'
    parent_layout = 'mailbox_common'
    header_widget = 'incoming_ack_header'
    footer_widget = 'incoming_ack_footer'

    def __init__(self, context, request):
        BrowserView.__init__(self, context, request)
        self.html_wid = widgetname(self.content_wid)
        # Would be slightly better to introspect theme page
        self.is_print = request.form.get('page') == 'Print'

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
        """Compute prefilled data.

        XXX hardcoded reference to parent's widget
        """
        doc = getattr(self, 'doc', None)
        if doc is None:
            doc = self.doc = self.context.getContent()
        mbox = aq_parent(aq_inner(self.context))
        if mbox.portal_type != 'Mailbox':
            header = footer = ''
        else:
            ltool = getToolByName(self.context, 'portal_layouts')
            layout = ltool[self.parent_layout]
            header = self._renderWidgetFor(layout[self.header_widget],
                                           proxy=mbox)
            footer = self._renderWidgetFor(layout[self.footer_widget])
        main = doc.render(cluster=self.prefill_cluster,
                          context=self.context,
                          layout_mode="view_ack",
                          proxy=self.context)
        return '\n'.join((header, main, footer))

    def _renderWidgetFor(self, widget, proxy=None):
        """Render a widget in view mode.

        If proxy is not specified, this assumes this isn't the first call.
        The previous one is used.
        """
        if proxy is not None:
            doc = proxy.getContent()
            dm = doc.getDataModel(proxy=proxy, context=proxy)
            self.parent_ds = DataStructure(datamodel=dm)
        widget.prepare(self.parent_ds)
        return widget.render('view', self.parent_ds)

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
                resp.redirect('%s?page=Print&mode=view_print' % url)
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
