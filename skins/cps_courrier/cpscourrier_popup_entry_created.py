##parameters=datastructure
"""
Do the necessary rendering or redirection after an entry has been
successfully created and filled with the initial values by the user.

The context is the directory.

May return a rendered document, or do a redirect.
"""

from urllib import urlencode

dirname = context.getId()
ou = datastructure.getDataModel().get('ou')

portal_url = context.portal_url()
args = {'dirname': dirname,
        'portal_status_message': 'psm_entry_created',
        'formaction': 'cpscourrier_popup_entry_create_form',
        }

if ou:
    args['widget__ou'] = 1

args = urlencode(args)

action_path = 'cpscourrier_popup_entry_create_form?'+args
context.REQUEST.RESPONSE.redirect('%s/%s' % (portal_url, action_path))

