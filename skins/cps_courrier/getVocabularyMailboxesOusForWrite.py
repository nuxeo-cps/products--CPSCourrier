##parameters=key=None
#$Id$
"""Return a vocabulary ou -> Mailbox Title

Used as MethodVocabulary in CPSCourrier paper."""

import logging
from AccessControl import getSecurityManager
logger = logging.getLogger('getVocabularyMailboxesOus')

logger.debug('key=%s', key)

l10n = context.translation_service
lang = l10n.getLanguage()

catalog = context.portal_catalog
query = {'portal_type': 'Mailbox',
         'language' : lang,
         }

if key is not None:
    query['ou'] = key
    brains = catalog(**query)
    if len(brains) != 1:
        return
    return brains[0].Title

if catalog.meta_type == 'CPS Lucene Catalog Tool':
    title_sort = 'Title_sort'
else:
    title_sort = 'Title'

query['sort-on'] = title_sort
brains = catalog(**query)

def intersects(list1, list2):
    """No set in restricted code (sigh)."""

    for x in list1:
        if x in list2:
            return True
    return False

write_roles = ['Contributor', 'Supervisor', 'LocalManager',
               'Injector', 'Manager']
user = getSecurityManager().getUser()

return [(brain.ou, brain.Title) for brain in brains
        if intersects(write_roles,
                      user.getRolesInContext(brain.getObject()))
        ]
