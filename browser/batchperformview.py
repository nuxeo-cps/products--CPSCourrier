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

from logging import getLogger, DEBUG

import transaction

from Acquisition import aq_inner, aq_parent

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CPSCore.EventServiceTool import getPublicEventService
from Products.CPSCourrier.workflows.scripts import reply_to_incoming
from Products.CPSUtil.session import sessionHasKey
from Products.CPSUtil.timer import Timer

from Products.CPSDashboards.browser.batchperformview import BatchPerformView as BaseBatchView

from Products.CPSDashboards.browser.searchview import SearchView

logger = getLogger('CPSCourrier.browser.batchperformview')

class BatchPerformView(BaseBatchView, SearchView):
    layout_id = 'mail_search_answers'

    session_key = "CPSCOURRIER_BATCH_PERFORM"

    submit_button_prefix = "cpsdashboards_batch_"

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

    def showSearchAnswerForm(self):
        """Decide whether we should display the transition confirmation form"""
        if self.action != 'answer':
            # No search for non answer actions
            return False
        if 'rpath' in self.request.form:
            # The template answer as already been chosen
            return False
        return True

    def showConfirmationForm(self):
        """Decide whether we should display the transition confirmation form"""
        if self.action != 'answer':
            # Non answer actions directly need the final confirmation form
            return True
        if 'rpath' in self.request.form:
            # The answering template is chosen, show the confirmation form
            return True
        return False

    def batchTriggerTransition(self, transition):
        """Do the WF update when possible and return the result as psm"""

        t = Timer('CPSCourrier.browser.batchperformview.batchTriggerTransition',
                  level=DEBUG)

        wftool = getToolByName(self.context, 'portal_workflow')
        portal = getToolByName(self.context, 'portal_url').getPortalObject()
        form = self.request.form

        kw = {
           'comment': form.get('comments', ''),
        }

        if transition == 'answer':
            # special case transition answer is a 2 steps transitions: first on
            # the incoming docs, then send the replies. In order to do so, we
            # will trigger the the reply_to_incoming wf script manually to
            # collect the replies of successful answers
            kw['no_reply_script'] = True

        if transition == 'handle':
            kw['group'] = form.get('group', '')
            kw['use_parent_roadmap'] = form.get('use_parent_roadmap', '')

        base_rpath = form.get('base_reply_rpath', '')

        t.mark('Process form data')

        failed = set()
        proxies = [portal.unrestrictedTraverse(rpath) for rpath in self.rpaths]

        t.mark('Grab proxies')

        for i, proxy in enumerate(proxies):
            wf = wftool.getWorkflowsFor(proxy)[0]

            if wf.isActionSupported(proxy, transition):
                wftool.doActionFor(proxy, transition, **kw)

                t.mark("Do action '%s' for proxy %d" % (transition, i))

                if transition == 'answer':
                    # step 2 creating the replies and triggering the send
                    # transition on them
                    reply = reply_to_incoming(proxy, base_rpath)

                    t.mark('Reply to incoming for proxy %d' % i)

                    wftool.doActionFor(reply, 'send', comment=kw['comment'])

                    t.mark("Do action 'send' for proxy %d" % i)

                # each proxy is independant, thus commit to avoid conflict
                # errors on portal_proxies between two batch performers
                transaction.commit()

                t.mark('Commit for proxy %d' % i)

            else:
                failed.add(proxy)


        # this is the end of the batch session
        self._expireSession()

        t.mark('Expire session')

        # compute the psm according to what was actually done
        psm = "psm_status_changed"
        mcat = getToolByName(self.context, 'translation_service')
        if failed:
            # translating psm here because no interpolation can be done at
            # display time for psms
            psm = mcat("psm_cpscourrier_no_action_performed_for")
            psm = psm.encode('iso-8859-15')
            psm += ', '.join(proxy.Title() for proxy in failed)

        t.mark('Compute psm')
        t.log()

        return self._doRedirect(psm)

    def replyPreview(self):
        """Render a textual preview of the mail that will be send"""
        utool = getToolByName(self.context, 'portal_url')
        portal = utool.getPortalObject()
        tstool = getToolByName(portal, 'translation_service')
        vtool = getToolByName(portal, 'portal_vocabularies')
        mtool = getToolByName(portal, 'portal_membership')
        encoding = portal.default_charset
        mcat = lambda label: tstool(label).encode(encoding)
        proxy = portal.unrestrictedTraverse(self.request.form.get('rpath'))
        doc = proxy.getContent()
        body = doc['content']
        foa = vtool.form_of_address.getMsgid(doc['form_of_address'])
        if foa:
            foa = mcat(foa)
        else:
            foa = vtool.form_of_address[doc['form_of_address']]
        user = mtool.getAuthenticatedMember()
        signature = mtool.getFullnameFromId(str(user))
        body += '\n\n%s\n\n-- \n%s' % (foa , signature)
        fake_original_msg = mcat('cpscourrier_fake_original_msg')
        return "%s\n\n%s" % (body,  fake_original_msg)
