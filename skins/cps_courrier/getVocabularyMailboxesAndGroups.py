##parameters=key=None
#$Id$
"""Return a portal type vocabulary, used as MethodVocabulary."""

# We use the list of types allowed in container as searchable types

catalog = context.portal_catalog
base_path = '/' + catalog.getPhysicalPath()[1] + '/'
types = ['Mailbox', ]
brains = catalog(portal_type=types,  path=base_path)
l10n = context.translation_service
res = [(base_path+brain.relative_path, brain.Title) for brain in brains]

res.insert(0, (base_path, l10n('cpscourrier_all_boxes').encode('iso-8859-15')))

if key is not None:
        res = [item[1] for item in res if item[0] == key][0]

return res
