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
from DateTime import DateTime
from Products.CMFCore.utils import getToolByName
from Products.CPSCourrier.workflow.scripts import send_mail

logger = logging.getLogger('CPSCourrier.dun')

class DunNotifier:

    # review states of proxies to be notified for (anything but trash or closed)
    review_states = ('received', 'handled', 'answering', 'answered')

    # portal types of proxies to be notified for
    portal_types = ('Incoming Mail',)

    # date attribute used to discriminate
    date_index_id = 'deadline'

    # maximum authorized delay between now and the document date
    date_tolerance = 0

    # sort criterion
    sort_on = 'deadline_sort'

    # local roles of members to get notified
    local_roles = ('LocalManager', 'Supervisor')

    # subject string to get localized
    subject = "cpscourrier_subject_${portal_title}_${mb_title}_${late_number}"

    # render method to render the body of the notification mail
    render_method = "cpscourrier_dun_notification_render"

    def __init__(self, portal):
        self._portal = portal
        self._catalog = getToolByName(portal, 'portal_catalog')
        mcat = getToolByName(portal, 'translation_service')
        self._mcat = lambda x: mcat(x).encode(portal.default_charset)

    def getLateMailDocuments(self, mailbox_rpath):
        """Generate lists of late documents brains

        This info is to be sent to the managers and supervisors of the mailbox
        """
        # limit search to the current mailbox rpath
        base_path = '/'.join(self._portal.getPhysicalPath())
        path = base_path + mailbox_rpath

        # maximum date
        date_max = DateTime() - self.tolerance

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
            'b_size': 100,
            'b_start': 0,
            # get latest mail documents first
            'sort-on': self.sort_on,
        }
        return self._catalog(**query)

    def getNotifieeEmails(self, mailbox):
        """Get the email address of people to be notified"""
        # TODO

    def notify(self):
        """Send email notifications to the manager of late documents"""
        query = {'portal_type': 'Mailbox'}
        for mb_brain in self._catalog(**query):
            late_docs_brains = self.getLateMailDocuments(mb_brain.relative_path)
            if late_docs_brains:
                mailbox = mb_brain.getObject()
                mfrom = self._portal.email_from_address
                mto = self.getNotifieeEmails(mailbox)
                info = {
                    'portal_title': self._portal.Title(),
                    'mb_title': mailbox.Title(),
                    'late_number': str(len(late_docs_brains)),
                }
                subject = self._mcat(self.subject, info)
                info.update({
                    'late_brains': late_docs_brains,
                    'portal_url': self._portal.absolute_url(),
                })
                body = self.portal[self.render_method](info)
                send_mail(self._portal, mto, mfrom, subject, body)



