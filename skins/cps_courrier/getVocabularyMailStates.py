##parameters=key=None
#$Id$
"""Return a portal type vocabulary, used as MethodVocabulary."""

# TODO: use same lookup as for portal_types and then ask corresponding wfs

# why a method if it's hardcoded? To put empty key *first
l10n = context.translation_service
vocitems = [(vkey, vkey) for vkey in ('pending', # not in CPSCourrier by default
                                      'received',
                                      'handled',
                                      'trash',
                                      'answering',
                                      'answered',
                                      'closed',
                                      'work',
                                      'locked',
                                      'draft',
                                      'validated',
                                      'sent')]
res = [(item[0], l10n(item[1]).encode('iso-8859-15'))
       for item in vocitems]

res.insert(0, ('', l10n('label_all').encode('iso-8859-15')))

if key is not None:
        res = [item[1] for item in res if item[0] == key][0]

return res
