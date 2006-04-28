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
from Products.CPSSkins.cpsskins_utils import (
    serializeForCookie, unserializeFromCookie)

from reuseanswerview import ReuseAnswerView

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
            transition =  transitions[0][len(self.submit_button_prefix):]

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

        if rpaths is ():
            # try to see if some rpaths where previously stored in cookies
            rpaths = self._readRpathsFromCookies()
        else:
            # rpaths were directly provided in the request, store them in
            # cookies for later reuse
            self._storeRpathsInCookies(rpaths)

        return rpaths

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

        if not self.rpaths:
            psm = 'psm_select_at_least_one_item'
            url = "%s?portal_status_message=%s" % (self.context.absolute_url(),
                                                   psm)
            self.request.RESPONSE.redirect(url)
            return 'do_redirect'

        # guess what is the transition to be performed in the current session
        self.transition = self._getTransitionId()
        if not self.transition:
            raise ValueError('No transition specified')

        trigger_transition = self.request.form.get('trigger_transition', None)
        if trigger_transition is not None:
            # handle the redirection and the psm
            self.batchTriggerTransition(trigger_transition)
            return 'do_redirect'

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
           'base_reply_rpath': form.get('base_reply_rpath', ''),
        }
        failed = []
        for rpath in self.rpaths:
            proxy = portal.unrestrictedTraverse(rpath)
            wf = wftool.getWorkflowsFor(proxy)[0]
            if wf.isActionSupported(proxy, transition):
                wftool.doActionFor(proxy, transition, **kw)
            else:
                failed.append(proxy.Title())

        # this is the end of the batch session: clean the cookies
        self._expireCookies()

        # compute the psm according to what was actually done
        psm = "psm_status_changed"
        mcat = getToolByName(self.context, 'translation_service')
        if failed:
            # translating psm here because no interpolation can be done at display
            # time for psms
            psm = mcat("psm_cpscourrier_no_action_performed_for")
            psm = psm.encode('iso-8859-15')
            psm += ', '.join(failed)

        url = "%s?%s" % (self.context.absolute_url(),
                         urlencode({'portal_status_message': psm}))
        self.request.RESPONSE.redirect(url)


