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
"""XML export of old threads of mail

This archiver assumes the catalog supports batching (ie is a lucene catalog).
"""

import logging
from DateTime import DateTime

from zExceptions import NotFound
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

        # set of a allowed states to speed up membership tests
        review_states = set(self.review_states)

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
            # process 100 proxies at a time: trade off between number of brains
            # loaded in memory and number of requests to the catalog
            'b_size': 100,
            'b_start': 0,
        }
        catalog = getToolByName(self._portal, 'portal_catalog')
        brains = catalog(**query)

        while brains:

            # record the set of rpath of proxies that where already processed to
            # avoid duplication
            rpaths_done = set()

            for brain in brains:
                if brain['relative_path'] in rpaths_done:
                    # already seen in a thread
                    continue

                try:
                    thread_seed = brain.getObject()
                except NotFound:
                    # the proxy has been deleted since last catalog query
                    continue

                thread_info = get_thread_for(thread_seed)
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

            # make the same query again starting with 0 as b_start cause
            # proxies may have been deleted since the last query
            brains = catalog(**query)
