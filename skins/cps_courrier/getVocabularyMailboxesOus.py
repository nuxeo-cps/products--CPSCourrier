##parameters=key=None
#$Id$
"""Return a portal type vocabulary, used as MethodVocabulary."""

import logging
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

return [(brain.ou, brain.Title) for brain in brains]
