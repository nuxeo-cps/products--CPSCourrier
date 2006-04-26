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

from urllib import urlencode

from Acquisition import aq_inner, aq_parent
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException

from reuseanswerview import ReuseAnswerView

class BatchPerformView(ReuseAnswerView):

    rapth = None # rpath of the reply to reuse if answering
    rpaths = () # rpaths of mails as target of the transition

    PREFIX = "cpscourrier_batch_"
    # namespace prefix for all the sublit buttons that call this view from a
    # mailbox or a dashboard listing

    def getTransitionId(self):
        """Compute the transition id from the request parameter"""
        form = self.request.form
        trans = [key for key in form if key.startswith(self.PREFIX)]
        if len(trans) > 1:
            raise ValueError("Got more than one transition to perform")
        elif not trans:
            return
        return trans[0][len(self.PREFIX):]

    def getMailInfo(self):
        """Compute data related to the rpath"""
        infos = []
        utool = getToolByName(self.context, 'portal_url')
        portal = utool.getPortalObject()
        for rpath in self.rpaths:
            mail_proxy = portal.unrestrictedTraverse(rpath)
            mailbox_proxy = aq_parent(aq_inner(mail_proxy))
            infos.append({
                'mail_title': mail_proxy.Title(),
                'mail_url': mail_proxy.absolute_url(),
                'mailbox_title': mailbox_proxy.Title(),
                'mailbox_url': mailbox_proxy.absolute_url(),
            })
        return infos

    def dispatchSubmit(self):
        """Process the POST request of the mailbox/dashboard listing views

        There are mainly two cases:
         - batch reply: reuse the reuse answer search form to trigger the
           reply wf script with the selected template as model
         - other batch transitions with a classical confirmation form
        """

        form = self.request.form

        # compute the list of incoming mail rpath and store them as attribute
        # of the view instance
        if 'ids' in form:
            utool = getToolByName(self.context, "portal_url")
            folder_rpath = utool.getRpath(self.context.aq_inner)
            self.rpaths = ['%s/%s' % (folder_rpath, id) for id in form['ids']]
        else:
            self.rpaths = form.get('rpaths', ())

        if not self.rpaths:
            psm = 'psm_select_at_least_one_item'
            url = "%s?portal_status_message=%s" % (self.context.absolute_url(),
                                                   psm)
            self.request.RESPONSE.redirect(url)
            return

        transition = form.get('trigger_transition', None)
        if transition is not None:
            # handle the redirection and the psm
            self.batchTriggerTransition(transition)
            return

    def batchTriggerTransition(self, transition):
        wftool = getToolByName(self.context, 'portal_workflow')
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        mcat = getToolByName(self.context, 'translation_service')
        comments = self.request.form.get('comments', '')
        failed = []
        for rpath in self.rpaths:
            proxy = portal.unrestrictedTraverse(rpath)
            try:
                wftool.doActionFor(proxy, transition, comment=comments)
            except WorkflowException:
                failed.append(proxy.Title())

        psm = "psm_status_changed"
        if failed:
            # translating psm here because no interpolation can be done at display
            # time for psms
            psm = mcat("psm_cpscourrier_no_action_performed_for")
            psm = psm.encode('iso-8859-15')
            psm += ', '.join(failed)

        url = "%s?%s" % (self.context.absolute_url(),
                         urlencode({'portal_status_message': psm}))
        self.request.RESPONSE.redirect(url)


