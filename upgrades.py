# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
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
# $Id$
"""upgrade steps handlers."""

import logging

import transaction

def up_0160_0170_mail_into_email(portal):
    """Take care of changes from the pure email to the paper/email aternative.
    """

    logger = logging.getLogger(
        'CPSCourrier.upgrades.up_0160_0170_mail_into_email')
    m_profiles = getattr(portal, 'meta_profiles', None)
    if m_profiles is not None and 'CourrierBase' in m_profiles:
        m_profiles += 'CourrierEmail'
        portal.manage_changeProperties(meta_profiles=m_profiles)
        logging.info("Added CourrierEmail in meta_profiles for replay.")

    # create new portal_types
    from Products.CPSDocument.FlexibleTypeInformation \
         import FlexibleTypeInformation
    ttool = portal.portal_types

    old_new = {'Incoming Mail': 'Incoming Email',
               'Outgoing Mail': 'Outgoing Email',
               }

    for old_id, new_id in old_new.items():
        fti = getattr(ttool, old_id)
        new_fti = FlexibleTypeInformation(new_id)
        new_fti.__dict__.update(fti.__dict__)
        ttool._setObject(new_id, new_fti)

    repotool = portal.portal_repository
    i = 1
    for doc in repotool.values():
        ptype = doc.portal_type
        if ptype in old_new:
            doc.portal_type = old_new[ptype]
        if i % 500 == 0:
            transaction.commit()
        i += 1
    logger.info("Changed portal_types for %d documents", i)

    # Catalog stuff
    # reindexation will be performed upon profile import.
    # No need to do it twice.
    cat = portal.portal_catalog
    if cat.meta_type == 'CPS Lucene Catalog Tool':
        cat.manage_clean()

    # delete old portal_types
    ttool.manage_delObjects(old_new.items())
