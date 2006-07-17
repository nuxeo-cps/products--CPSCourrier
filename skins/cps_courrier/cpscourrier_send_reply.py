##parameters=REQUEST=None, **kw

form = REQUEST.form

from Products.CMFCore.utils import getToolByName
wtool = getToolByName(context, "portal_workflow")

comment = form.get('comments', '')

if form.get('submit_template'):
    wtool.doActionFor(context, 'copy_submit',
                      comment=comment,
                      dest_container='mail_templates',
                      initial_transition='submit')

try:
    wtool.doActionFor(context, 'send', comment=comment, **form)
    psm = "psm_cpscourrier_reply_sent"
except IOError:
    psm = "psm_cpscourrier_reply_could_not_be_sent"
except ValueError, e:
    psm = "psm_cpscourrier_reply_could_not_be_sent_%s" % e

if REQUEST is not None:
    url = "%s?portal_status_message=%s" % (context.absolute_url(), psm)
    REQUEST.RESPONSE.redirect(url)

