##parameters=workflow_action, workflow_action_form, current_var_id='', REQUEST=None
# $Id$

from zLOG import LOG, DEBUG

kw = {
    'current_wf_var_id' : current_var_id,
    }
context.portal_workflow.doActionFor(context, workflow_action, **kw)
psm = 'psm_level_changed'

if REQUEST is not None:
    url = '%s?portal_status_message=%s' % (context.absolute_url(), psm)
    LOG("content_assignment_level_move", DEBUG, "url=%s"%(url,))
    REQUEST.RESPONSE.redirect(url)
