##parameters=key=None
#$Id$
"""Return the vocabulary rpath -> title of all mailboxes.

Used for filters in dashboards and advanced search."""

# We use the list of types allowed in container as searchable types

import logging
logger = logging.getLogger('getVocabularyMailboxesAndGroups')

logger.debug('key=%s', key)

tree = context.portal_trees.mailboxes
types = ['Mailbox', ]

l10n = context.translation_service
res = [(tree_el['rpath'], tree_el['title'])
       for tree_el in tree.getList()
       if tree_el['portal_type'] in types]

# XXX should go now that Select Widget can cope
res.insert(0, ('', l10n('cpscourrier_all_boxes').encode('iso-8859-15')))

if key is not None:
    match = [item[1] for item in res if item[0] == key]
    if match: # found
        res = match[0]
    else: # not found
        res = res[0][1]

return res
