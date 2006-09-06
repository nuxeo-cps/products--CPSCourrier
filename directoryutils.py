# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
# Author: Georges Racinet <gracinet@nuxeo.com>
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

#$Id$

import logging
from AccessControl import getSecurityManager
from Products.CMFCore.utils import getToolByName

logger = logging.getLogger('CPSCourrier.directoryutils')

def hasLocalAddressBookRole(portal, ou, role):
    """Tell if the user has the given role on the mailbox with given ou.

    Implementation assumes the catalog is quick on small indexes, no matter
    how big the whole database is.
    """

    catalog = getToolByName(portal, 'portal_catalog')
    brains = catalog(ou=ou)

    if not brains:
        # most probably user has no view perm
        return False
    if len(brains) > 1:
        logger.warn("More than one mailbox with ou=%s", ou)

    mailbox = brains[0].getObject()
    user = getSecurityManager().getUser()
    return user.has_role(role, mailbox)
