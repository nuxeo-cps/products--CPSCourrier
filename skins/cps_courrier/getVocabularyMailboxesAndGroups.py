##parameters=key=None
#$Id$
"""Return a portal type vocabulary, used as MethodVocabulary."""

# We use the list of types allowed in container as searchable types

import logging
logger = logging.getLogger('getVocabularyMailboxesAndGroups')

logger.debug('key=%s', key)

tree = context.portal_trees.mailboxes
portal = context.portal_url.getPortalObject()
base_path = '/'.join(portal.getPhysicalPath())
types = ['Mailbox', ]

l10n = context.translation_service
res = [('/'.join((base_path, tree_el['rpath'])), tree_el['title'])
       for tree_el in tree.getList()
       if tree_el['portal_type'] in types]
res.insert(0, (base_path, l10n('cpscourrier_all_boxes').encode('iso-8859-15')))

if key is not None:
    match = [item[1] for item in res if item[0] == key]
    if match: # found
        res = match[0]
    else: # not found
        res = res[0][1]

return res
