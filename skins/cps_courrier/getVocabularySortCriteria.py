##parameters=key=None
#$Id$
"""Return a portal vocabulary of relevent sort keys in mail related dashboards.

Used as MethodVocabulary. Should be aggressively cached (static in prod)"""

ltool = context.portal_layouts
layout = ltool['mail_dashboard_row']

sortables = [wi for wi in layout.objectValues() if getattr(wi, 'sortable', '')]

l10n = context.translation_service
# use index id as key and column header as msg
res = [(wi.sortable,
	(not wi.is_i18n and wi.label) or l10n(wi.label).encode('iso-8859-15'))
       for wi in sortables]

res.insert(0, ('', l10n('label_none').encode('iso-8859-15')))

if key is not None:
        res = [item[1] for item in res if item[0] == key][0]

return res
