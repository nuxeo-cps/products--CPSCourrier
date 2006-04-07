##parameters=workflow_action, rpaths, comments='', REQUEST=None
"""Perform transition triggering in batch mode
"""

from Products.CMFCore.WorkflowCore import WorkflowException
from urllib import urlencode

wtool = context.portal_workflow
mcat = context.translation_service
failed = []

for rpath in rpaths:
    proxy = context.restrictedTraverse(rpath)
    try:
        wtool.doActionFor(proxy, workflow_action, comment=comments)
    except WorkflowException:
        failed.append(proxy.Title())

psm = "psm_status_changed"
if failed:
    # translating first cause no interpolation can be done at display time for
    # psms
    psm = mcat("psm_cpscourrier_no_action_performed_for").encode('iso-8859-15')
    psm += ', '.join(failed)

if REQUEST is not None:
    url = "%s?%s" % (
        context.absolute_url(), urlencode({'portal_status_message': psm}))
    REQUEST.RESPONSE.redirect(url)

