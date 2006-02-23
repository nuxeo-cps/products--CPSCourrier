##parameters=key=None
#$Id$
"""Return a portal type vocabulary, used as MethodVocabulary."""

# We use the list of types allowed in container as searchable types

ttool = context.portal_types
type_ids = ttool[context.portal_type].allowed_content_types
types = [ttool[tid] for tid in type_ids]

l10n = context.translation_service
res = [(item.getId(), l10n(item.Title()).encode('iso-8859-15'))
       for item in types]

res.insert(0, ('', l10n('label_all').encode('iso-8859-15')))

if key is not None:
        res = [item[1] for item in res if item[0] == key][0]

return res
