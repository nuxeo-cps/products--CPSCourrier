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
from logging import getLogger

from Acquisition import aq_inner, aq_parent
from OFS.CopySupport import CopyError
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException
from Products.CPSCore.EventServiceTool import getPublicEventService
from Products.CPSSkins.cpsskins_utils import (
    serializeForCookie, unserializeFromCookie)
from Products.CPSCourrier.workflows.scripts import reply_to_incoming

from reuseanswerview import ReuseAnswerView

logger = getLogger('CPSCourrier.browser.batchperformview')

class BatchPerformView(ReuseAnswerView):

    transition = None # id of the wf action to be performed
    rapth = None # rpath of the reply to reuse if answering
    rpaths = () # rpaths of mails as target of the transition

    rpaths_cookie_prefix = "cpscourrier_batch_perform_rpath_"
    transition_cookie_id = "cpscourrier_batch_perform_transition"

    submit_button_prefix = "cpscourrier_batch_"
    # namespace prefix for all the submit buttons that call this view from a
    # mailbox or a dashboard listing

    #
    # Helpers to manage cookies and maintain current session
    #

    def _getTransitionId(self):
        """Compute the transition id from the request parameter and store the
        result in a cookie"""
        transition = ''

        form = self.request.form

        transitions = [key for key in form
                           if key.startswith(self.submit_button_prefix)]
        if len(transitions) > 1:
            raise ValueError("Got more than one transition to perform")
        if transitions:
            transition = transitions[0][len(self.submit_button_prefix):]

        if 'answer_submit' in form:
            transition =  'answer'

        # cookie management
        path = self.request['URLPATH1']
        cookie_id = self.transition_cookie_id

        if transition:
            # a transition id could be read from the request, store it in a
            # cookie for further reuse
            self.request.RESPONSE.setCookie(cookie_id,
                                            serializeForCookie(transition),
                                            path=path)
        else:
            # try to read matching cookie if any
            cookies = self.request.cookies
            transition = str(unserializeFromCookie(cookies.get(cookie_id, '')))
        return transition

    def _storeRpathsInCookies(self, rpaths):
        """Store selected rpaths on the client browser """
        path = self.request['URLPATH1']
        cookies = self.request.cookies
        response = self.request.RESPONSE
        old = set(id for id in cookies
                     if id.startswith(self.rpaths_cookie_prefix))
        # store or update rapths
        new = set()
        for i, rpath in enumerate(rpaths):
            cookie_id = "%s%03d" % (self.rpaths_cookie_prefix, i)
            response.setCookie(cookie_id, serializeForCookie(rpath), path=path)
            new.add(cookie_id)

        # clean potential old cookies that were not cleaned elsewhere
        for cookie_id in old - new:
            response.expireCookie(cookie_id, path=path)

    def _readRpathsFromCookies(self):
        """Read the request to find rpaths cookies

        Restricted to those that match potential stored rpaths for the current
        mailbox
        """
        cookies = self.request.cookies.items()
        return [str(unserializeFromCookie(cookie)) for c_id, cookie in cookies
                    if c_id.startswith(self.rpaths_cookie_prefix)]

    def _expireCookies(self):
        """Expire cookies related to the current mailbox"""
        path = self.request['URLPATH1']
        cookies = self.request.cookies
        response = self.request.RESPONSE
        for cookie_id in cookies:
            if cookie_id.startswith(self.rpaths_cookie_prefix):
                response.expireCookie(cookie_id, path=path)
        if self.transition_cookie_id in cookies:
            response.expireCookie(self.transition_cookie_id, path=path)

    def _getMailRpaths(self):
        """Process the request to extract the list of rpath of selected mails

        Also take care of storing/reading/updating the cookie if necessary
        """
        form = self.request.form

        # read the request data

        if 'ids' in form:
            utool = getToolByName(self.context, "portal_url")
            folder_rpath = utool.getRpath(self.context.aq_inner)
            rpaths =  ['%s/%s' % (folder_rpath, id) for id in form['ids']]
        else:
            rpaths = form.get('rpaths', ())

        # cookies management

        # are we at the first call of the batch form or inside a multi screen
        # session?
        init_call = False
        for key in form:
            if key.startswith(self.submit_button_prefix):
                init_call = True
                break

        if not rpaths and not init_call:
            # nothing was provided in the request, we are probably in a multi
            # screens session:
            # try to see if some rpaths where previously stored in cookies
            rpaths = self._readRpathsFromCookies()
        else:
            # rpaths were directly provided in the request, store them in
            # cookies for later reuse
            self._storeRpathsInCookies(rpaths)

        logger.debug('rpaths: %s' % (rpaths,))
        return rpaths

    #
    # Cut copy paste management
    #

    def _doRedirect(self, psm):
        url = "%s?%s" % (self.context.absolute_url(),
                         urlencode({'portal_status_message': psm}))
        self.request.RESPONSE.redirect(url)
        # return a flag that tells the template not to render the rest of the
        # view since we don't need it
        return 'do_redirect'

    def _doCutCopyPaste(self):
        """Special handling of cut/copy/paste actions

        This are not actual transitions and require special treatment
        """
        if self.transition == 'paste':
            if self.context.cb_dataValid:
                cp = self.request['__cp']
                try:
                    result = self.context.manage_CPSpasteObjects(cp)
                    for id in [ob['new_id'] for ob in result]:
                        ob = getattr(self.context, id)
                        evtool = getPublicEventService(self.context)
                        evtool.notifyEvent('workflow_cut_copy_paste', ob, {})
                    psm = 'psm_item(s)_pasted'
                except CopyError:
                    psm = 'psm_copy_or_cut_at_least_one_document'
                except WorkflowException:
                    psm = 'psm_operation_not_allowed'
            else:
                psm = 'psm_copy_or_cut_at_least_one_document'
        else:
            # copy or cut
            ids = [rpath.rsplit('/', 1)[1] for rpath in self.rpaths]
            if ids:
                if self.transition == 'cut':
                    self.context.manage_CPScutObjects(ids, self.request)
                    psm = 'psm_item(s)_cut'
                if self.transition == 'copy':
                    self.context.manage_CPScopyObjects(ids, self.request)
                    psm = 'psm_item(s)_copied'
            else:
                psm = 'psm_select_at_least_one_document'

        return self._doRedirect(psm)

    #
    # View API for the template
    #

    def dispatchSubmit(self):
        """Process the POST request of the mailbox/dashboard listing views

        There are mainly two cases:
         - batch reply: reuse the reuse answer search form to trigger the
           reply wf script with the selected template as model
         - other batch transitions with a classical confirmation form
        """
        # compute the list of incoming mail rpath and store them as attribute
        # of the view instance
        self.rpaths = self._getMailRpaths()

        # guess what is the transition to be performed in the current session
        self.transition = self._getTransitionId()
        if not self.transition:
            raise ValueError('No transition specified')

        if self.transition in ('cut', 'copy', 'paste'):
            # special actions that are not handled by actual workflow
            # transitions
            return self._doCutCopyPaste()

        if not self.rpaths:
            return self._doRedirect('psm_select_at_least_one_item')

        trigger_transition = self.request.form.get('trigger_transition', None)
        if trigger_transition is not None:
            # handle the redirection and the psm
            return self.batchTriggerTransition(trigger_transition)

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
        if self.transition != 'answer':
            # No search for non answer transitions
            return False
        if 'rpath' in self.request.form:
            # The template answer as already been chosen
            return False
        return True

    def showConfirmationForm(self):
        """Decide whether we should display the transition confirmation form"""
        if self.transition != 'answer':
            # Non answer transitions directly need the final confirmation form
            return True
        if 'rpath' in self.request.form:
            # The answering template is chosen, show the confirmation form
            return True
        return False

    def batchTriggerTransition(self, transition):
        """Do the WF update when possible and return the result as psm"""

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

        failed = set()
        proxies = [portal.unrestrictedTraverse(rpath) for rpath in self.rpaths]
        for proxy in proxies:
            wf = wftool.getWorkflowsFor(proxy)[0]
            if wf.isActionSupported(proxy, transition):
                wftool.doActionFor(proxy, transition, **kw)
            else:
                failed.add(proxy)

        if transition == 'answer':
            # step 2 creating the replies and triggering the send transition on
            # them
            replies = []
            base_rpath = form.get('base_reply_rpath', '')
            replies = [reply_to_incoming(p, base_rpath) for p in proxies
                                                        if p not in failed]
            for reply in replies:
                wftool.doActionFor(reply, 'send', comment=kw['comment'])

        # this is the end of the batch session: clean the cookies
        self._expireCookies()

        # compute the psm according to what was actually done
        psm = "psm_status_changed"
        mcat = getToolByName(self.context, 'translation_service')
        if failed:
            # translating psm here because no interpolation can be done at
            # display time for psms
            psm = mcat("psm_cpscourrier_no_action_performed_for")
            psm = psm.encode('iso-8859-15')
            psm += ', '.join(proxy.Title() for proxy in failed)
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



