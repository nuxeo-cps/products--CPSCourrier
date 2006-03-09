##parameters=workflow_action, workflow_action_form, current_var_id, change_type, get_level=0, level=None, push_ids=[], pop_ids=[], search_term='', search_param='', comment='', REQUEST=None
# $Id$

from zLOG import LOG, DEBUG
from urllib import urlencode

old_state = context.portal_workflow.getInfoFor(context, 'review_state', None)

err = 0

if change_type == 'push':
    if get_level and level is None:
        psm = 'psm_select_a_level'
        err = 1
    else:
        if not push_ids:
            psm = 'psm_select_at_least_one_item'
            err = 1
        else:
            kw = {
                'push_ids': push_ids,
                'current_wf_var_id' : current_var_id,
                'comment': comment,
                }
            # get levels for selected users
            if get_level:
                kw['levels'] = len(push_ids)*[level]
            context.portal_workflow.doActionFor(context, workflow_action, **kw)
            psm = 'psm_delegation_changed'
elif change_type == 'pop':
    if not pop_ids:
        psm = 'psm_select_at_least_one_item'
        err = 1
    else:
        kw = {
            'pop_ids' : pop_ids,
            'current_wf_var_id' : current_var_id,
            'comment': comment,
            }
        context.portal_workflow.doActionFor(context, workflow_action, **kw)
        psm = 'psm_delegation_changed'

if REQUEST is not None:
    # if object is not is the same state, do not redirect to the
    # workflow_action_form page but to the object view page because transition
    # names will not be the same in a different state
    page_template = workflow_action_form
    new_state = context.portal_workflow.getInfoFor(context, 'review_state', None)
    if old_state != new_state:
        page_template = 'view'
    kwargs = {
        'workflow_action': workflow_action,
        'current_var_id': current_var_id,
        'portal_status_message': psm,
        }
    if err == 1:
        kwargs.update({
            'search_param': search_param,
            'search_term': search_term,
            'comment': comment,
            })
    kwargs = urlencode(kwargs)
    redirect_url = '%s/%s?%s'%(context.absolute_url(), page_template, kwargs)
    REQUEST.RESPONSE.redirect(redirect_url)

