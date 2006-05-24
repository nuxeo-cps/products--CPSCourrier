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
"""XML export of old threads of mail"""

import logging
from DateTime import DateTime

from Products.CMFCore.utils import getToolByName
from Products.CPSCourrier.config import ARCHIVE_MIN_AGE, ARCHIVE_HOME
from Products.CPSCourrier.relations import get_thread_for

logger = logging.getLogger('CPSCourrier.archive')


class Archiver:

    # review states of proxies to be archived
    review_states = ['closed', 'trash', 'sent']

    # portal types of proxies to be archived
    portal_types = ['Incoming Mail', 'Outgoing Mail']

    def __init__(self, portal):
        self._portal = portal

    def getThreadsToArchive(self):
        """Generate lists of proxies that are to be archived

        A proxy is to be archived if the whole thread of related mails are
        either in state closed, trash or sent and older that ARCHIVE_MIN_AGE.

        Candidate proxies are found thanks to a catalog search.
        """
        # record the set of rpath of proxies that where already processed to
        # avoid duplication
        rpaths_done = set()

        # maximum creation date
        created_max = DateTime() - ARCHIVE_MIN_AGE

        # find candidate proxies for archiving
        query = {
            'portal_type': self.portal_types,
            'review_state': self.review_states,
            'created': {
                'query': created_max,
                'range': 'max',
            },
        }
        # XXX refactore! use batching to avoid having 100 000 RSS items to parse
        brains = getToolByName(self._portal, 'portal_catalog')(**query)

        review_states = set(self.review_states)

        for brain in brains:
            if brain['relative_path'] in rpaths_done:
                # already seen in a thread
                continue

            thread_info = get_thread_for(brain.getObject())
            proxies = []
            invalid_thread = False

            for _, proxy_info in thread_info:
                rpaths_done.add(proxy_info['rpath'])
                proxy = proxy_info['object']
                if proxy_info['review_state'] not in review_states:
                    invalid_thread = True
                    break
                if proxy.getContent()['created'] > created_max:
                    invalid_thread = True
                    break
                proxies.append(proxy)

            if not invalid_thread:
                logger.debug('Next thread to archive: %s' % proxies)
                yield proxies
