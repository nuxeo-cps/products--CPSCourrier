##parameters=target_mailbox, REQUEST=None
from ZTUtils import make_query

if not target_mailbox:
    return

base_url = context.portal_url.getBaseUrl()
query = {'type_name': 'Incoming Pmail'}
url = '%s%s/cpsdocument_create_form?%s' % (base_url,
                                           target_mailbox,
                                           make_query(query),
                                           )

if REQUEST is not None:
    REQUEST.RESPONSE.redirect(url)
