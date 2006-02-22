##parameters=key=None
#$Id$
"""Return a portal type vocabulary, used as MethodVocabulary."""

# This is taken from CPSDefault's getVocabularySearchPortalType.py
# modifications: allowed=1, decode

types = context.getSortedContentTypes(allowed=1)
l10n = context.translation_service
res = [(item.getId(), l10n(item.Title()).encode('iso-8859-15'))
       for item in types]

res.insert(0, ('', l10n('label_all').encode('iso-8859-15')))

if key is not None:
        res = [item[1] for item in res if item[0] == key][0]

return res
