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

from Products.CMFCore.utils import getToolByName

from searchview import SearchView

logger = logging.getLogger('CPSCourrier.browser.reuseanswerview')

class ReuseAnswerView(SearchView):

    layout_id = 'mail_search_answers'

    def dispatchSubmit(self):
        """take submissions, calls skins scripts, etc.

        returns rendered html, empty meaning no script called.

        XXX this seems to be called twice as expected. Investigate."""

        form = self.request.form

        form.pop('-C', None) # polluting key from publisher

        if 'answer_submit' in form and 'rpath' in form:
            wftool = getToolByName(self.context, 'portal_workflow')
            # takes care of redirection as well
            wftool.doActionFor(self.context, 'answer',
                               base_reply_rpath=form['rpath'])
            return True
        else: # filtering or no submission at all
            return ''

        meth = getattr(context, method)
        return meth(REQUEST=self.request)

