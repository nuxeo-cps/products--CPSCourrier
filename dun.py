# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
# Author: Olivier Grisel <ogrisel@nuxeo.com>
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
"""Email notifications for late mail documents

For each Mailbox and for each supervisor/manager, send a notification with all
late mails.
"""

import logging
from AccessControl import Unauthorized
from DateTime import DateTime
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import _checkPermission
from Products.CPSUtil.mail import send_mail

logger = logging.getLogger('CPSCourrier.dun')

class DunNotifier:

    # review states of proxies to be notified for (anything but trash or closed)
    review_states = ('received', 'handled', 'answering', 'answered')

    # portal types of proxies to be notified for
    portal_types = ('Incoming Email', 'Incoming Pmail')

    # date attribute used to discriminate
    date_index_id = 'deadline'

    # maximum authorized delay between now and the document date
    date_tolerance = 0

    # sort criterion
    sort_on = 'deadline_sort'

    # local roles of members to get notified
    notified_roles = set(['LocalManager', 'Supervisor'])

    # subject string to get localized
    subject = "cpscourrier_subject_${portal_title}_${mb_title}_${late_number}"

    # max number of late emails to report
    sort_limit = 100

    # render method to render the body of the notification mail
    render_method = "cpscourrier_dun_notification_render"

    def __init__(self, portal):
        if not _checkPermission(ManagePortal, portal):
            raise Unauthorized
        self._portal = portal
        self._catalog = getToolByName(portal, 'portal_catalog')
        self._transl = getToolByName(portal, 'translation_service')

        aclu = getToolByName(portal, 'acl_users')
        dtool = getToolByName(portal, 'portal_directories')
        self._mdir = dtool[aclu.users_dir]
        self._gdir = dtool[aclu.groups_dir]

    def _mcat(self, x, param_dict=None):
        return self._transl(x, param_dict)

    def getLateMailDocuments(self, mailbox_rpath):
        """Generate lists of late documents brains

        This info is to be sent to the managers and supervisors of the mailbox
        """
        # limit search to the current mailbox rpath
        base_path = '/'.join(self._portal.getPhysicalPath())
        path = base_path + mailbox_rpath

        # maximum date
        date_max = DateTime() - self.date_tolerance

        # find candidate proxies for archiving
        query = {
            'path': path,
            'portal_type': self.portal_types,
            'review_state': self.review_states,
            self.date_index_id: {
                'query': date_max,
                'range': 'max',
            },
            # limit the number of results to 100
            'sort-limit': self.sort_limit,
            # get latest mail documents first
            'sort-on': self.sort_on,
        }
        return self._catalog(**query)

    def appendUserEmail(self, em_list, user_id):
        entry = self._mdir._getEntry(user_id, default=None)
        if entry is None:
            warn="Non-existent user %s has matching roles. Reindex security?"
            logger.warn(warn, user_id)
            return
        email = entry.get('email')
        if email is None:
            logger.error(
                "Directory entry for user %s has no email", user_id)
            return
        em_list.append(email)

    def getNotifieeEmails(self, mailbox):
        """Get the email address of people to be notified"""

        notifiees = []

        mtool = getToolByName(self._portal, 'portal_membership')
        roles_info =  mtool.getMergedLocalRoles(mailbox)
        members_ids = [mid for mid, m_roles in roles_info.items()
                       if self.notified_roles.intersection(m_roles)]
        for mid in members_ids:
            pref = 'user:'
            if mid.startswith(pref):
                user_id = mid[len(pref):]
                self.appendUserEmail(notifiees, user_id)

            pref = 'group:'
            if mid.startswith(pref):
                group_id =  mid[len(pref):]
                group = self._gdir._getEntry(group_id, default=None)
                if group is None:
                    logger.warn("Non-existent group %s has roles on %s.")
                    continue
                for user_id in group['members']:
                    self.appendUserEmail(notifiees, user_id)
        return notifiees

    def notify(self):
        """Send email notifications to the manager of late documents"""
        query = {'portal_type': 'Mailbox'}
        report = []
        for mb_brain in self._catalog(**query):
            late_docs_brains = self.getLateMailDocuments(mb_brain.relative_path)
            if late_docs_brains:
                mailbox = mb_brain.getObject()
                if mailbox is None:
                    continue
                mfrom = self._portal.email_from_address
                mto = self.getNotifieeEmails(mailbox)
                if not mto:
                    continue

                info = {
                    'portal_title': self._portal.Title(),
                    'mb_title': mailbox.Title(),
                    'mb_url': mailbox.absolute_url(),
                    'late_number': str(len(late_docs_brains)),
                    'sort_limit': self.sort_limit,
                }
                subject = self._mcat(self.subject, info)
                info.update({
                    'late_brains': late_docs_brains,
                    'portal_url': self._portal.absolute_url(),
                })
                body = self._portal[self.render_method](**info)
                send_mail(self._portal, mto, mfrom, subject, body,
                          plain_text=False)
                info['notifiees'] = mto
                report.append(info)
        return report
