##parameters=REQUEST=None
"""Return the list of translated titles and rpath for all Mailboxes on the
portal without security checks

This is used by the mail forward feature.
"""

mailboxes_cache = context.portal_trees.mailboxes
mcat = context.translation_service
locale = mcat.getSelectedLanguage()

cached = mailboxes_cache.getList(
    filter=False,
    locale_keys=('title'),
    locale_lang=locale,
)

mb_list = [('', mcat('cpscourrier_no_mailbox').encode('iso-8859-15'))]
mb_list += [(info['rpath'], info['title']) for info in cached
                                           if info['portal_type'] == 'Mailbox']
return mb_list
