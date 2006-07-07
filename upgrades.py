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

def zCatalogUpdateProxiesPType(catalog, mapping):
    """Update portal_type of all proxies. Use the given catalog for lookup."""
    raise NotImplementedError

def luceneUpdateProxiesPType(catalog, old_new):
    """Update portal_type of all proxies by leveraging Lucene batching .

    old_new is a mapping: old portal_type -> new one
    Doesn't reindex anything. A profile import is supposed to do it anyway.
    Cleans the store.
    """
    import pdb; pdb.set_trace()
    b_start = 0
    b_size = 500
    total = 0
    brains = True # initiate loop
    while brains:
        brains = catalog._search(portal_type=old_new.keys(),
                                 b_start=b_start, b_size=b_size)
        b_start += len(brains)
        if brains:
            total = brains[0].out_of
        for brain in brains:
            proxy = brain.getObject()
            if proxy is not None:
                old = proxy.portal_type
                # could have been already changed because of lang revs
                proxy.portal_type = old_new.get(old, old)
                # doesn't reindex and this is what we want
        transaction.commit()

#    catalog.manage_clean() # would be nice to clean just one index.
    return total

def up_0160_0170_mail_into_email(portal):
    """Take care of changes from the pure email to the paper/email aternative.
    """

    logger = logging.getLogger(
        'CPSCourrier.upgrades.up_0160_0170_mail_into_email')
    m_profiles = getattr(portal, 'meta_profiles', None)
    if m_profiles is not None and 'CourrierBase' in m_profiles \
       and 'CourrierEmail' not in m_profiles:

        m_profiles = list(m_profiles)
        i = m_profiles.index('CourrierBase')
        m_profiles.insert(i+1, 'CourrierEmail')

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
        fti = getattr(ttool, old_id, None)
        if fti is None:
            continue

        fti.getId() # force lazy __dict__ to work
        attrs = fti.__dict__.copy()
        del attrs['id']
        new_fti = FlexibleTypeInformation(new_id)
        new_fti.__dict__.update(attrs)

        ttool._setObject(new_id, new_fti)

    # upgrading proxies (safer to do them first)
    cat = portal.portal_catalog
    if cat.meta_type == 'CPS Lucene Catalog Tool':
        n_proxies = luceneUpdateProxiesPType(cat, old_new)
    else:
        n_proxies = zCatalogUpdateProxiesPtype(cat, old_new)
    logger.info("Changed portal_type for %d proxies", n_proxies)

    # upgrading repository documents
    repotool = portal.portal_repository
    i = 0
    for doc in repotool.values():
        ptype = doc.portal_type
        if ptype in old_new:
            doc.portal_type = old_new[ptype]
            i += 1
            if i % 500 == 0:
                transaction.commit()
    logger.info("Changed portal_type for %d documents", i)

    # delete old portal_types
    ftis = ttool.objectIds()
    remaining = [old_id for old_id in old_new.keys() if old_id not in ftis]
    ttool.manage_delObjects(remaining)
