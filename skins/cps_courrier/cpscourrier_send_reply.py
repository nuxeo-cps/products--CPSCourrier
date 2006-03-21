##parameters=REQUEST=None, **kw

from Products.CMFCore.utils import getToolByName
wtool = getToolByName(context, "portal_workflow")

try:
    wtool.doActionFor(context, 'send', comments=kw.get('comments', ''))
    psm = "psm_cpscourrier_reply_sent"
except IOError:
    psm = "psm_cpscourrier_reply_could_not_be_sent"

if REQUEST is not None:
    url = "%s?portal_status_message=%s" % (context.absolute_url(), psm)
    REQUEST.RESPONSE.redirect(url)

