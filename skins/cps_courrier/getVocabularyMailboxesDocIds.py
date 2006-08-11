##parameters=key=None
#$Id$
"""Return a portal type vocabulary, used as MethodVocabulary."""

import logging
logger = logging.getLogger('getVocabularyMailboxesDocIds')

logger.debug('key=%s', key)

l10n = context.translation_service
lang = l10n.getLanguage()

if key is not None:
    pxtool = context.portal_proxies
    try:
        info = pxtool.getProxyInfosFromDocid(key)[0]
    except KeyError, IndexError:
        return
    return info['visible'] and info['object'].title_or_id() or None

# we use the catalog, because TreeCache doesn't store docids
# catalog also nicer than proxy tool to get title sorting and so-on
catalog = context.portal_catalog
if catalog.meta_type == 'CPS Lucene Catalog Tool':
    title_sort = 'Title_sort'
else:
    title_sort = 'Title'

query = {'portal_type': 'Mailbox',
         'language' : lang,
         'sort-on' : title_sort,
         }

brains = catalog(**query)
# XXX getObject bad for perf.
return [(brain.getObject().getDocid(), brain.Title) for brain in brains]
