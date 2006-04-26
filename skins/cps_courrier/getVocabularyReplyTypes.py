##parameters=key=None
#$Id$
"""Return a portal type vocabulary, used as MethodVocabulary."""

# reply types depend actually on location only

utool = context.portal_url
portal = utool.getPortalObject()
base_path = '/' + utool.getPhysicalPath()[1] + '/'
res = [('mailboxes', 'cpscourrier_simple_reply'),
       ('mail_templates', 'cpscourrier_mail_template')]

l10n = context.translation_service
res = [(base_path+id, l10n(title)) for id, title in res]

res.insert(0, (base_path, l10n('label_all').encode('iso-8859-15')))

if key is not None:
    match = [item[1] for item in res if item[0] == key]
    if match: # found
        res = match[0]
    else: # not found
        res = res[0][1]

return res
