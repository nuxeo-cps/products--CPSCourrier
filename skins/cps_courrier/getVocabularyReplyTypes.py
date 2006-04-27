##parameters=key=None
#$Id$
"""Return a portal type vocabulary, used as MethodVocabulary."""

# reply types depend actually on location only
# XXX should be done with a static voc and insertion of empty key but
# this didn't work last time I tried

res = [('mailboxes', 'cpscourrier_simple_reply'),
       ('mail_templates', 'cpscourrier_mail_template')]

l10n = context.translation_service
res = [(id, l10n(title)) for id, title in res]

res.insert(0, ('', l10n('label_all').encode('iso-8859-15')))

if key is not None:
    match = [item[1] for item in res if item[0] == key]
    if match: # found
        res = match[0]
    else: # not found
        res = res[0][1]

return res
