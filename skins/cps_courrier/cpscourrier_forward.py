##parameters=target_mailbox='', target_emailaddress='', comments='', REQUEST=None

url = None
redirect_to_template = '' # redirect to view by default
wftool = context.portal_workflow

kw = {'comment': comments}

if target_mailbox and target_emailaddress:
    psm = "psm_cpscourrier_choose_either_mailbox_or_emailaddress"
    workflow_action = None
    redirect_to_template = 'cpscourrier_forward_form'

elif target_mailbox:
    psm = 'psm_cpscourrier_mail_forwarded'
    workflow_action = 'forward_move'
    kw['dest_container'] = target_mailbox
    kw['initial_transition'] = 'create_forward'

elif target_emailaddress:
    psm = 'psm_cpscourrier_mail_forwarded'
    workflow_action = 'forward_email'
    kw['target_emailaddress'] = target_emailaddress

else:
    psm = "psm_cpscourrier_choose_at_least_mailbox_or_emailaddress"
    workflow_action = None
    redirect_to_template = 'cpscourrier_forward_form'


if workflow_action is not None:
    res = wftool.doActionFor(context, workflow_action, **kw)


if REQUEST is not None:
    folder = context.aq_inner.aq_parent
    id = context.getId()
    if id in folder.objectIds():
        url = context.absolute_url()
    else:
        url = folder.absolute_url()
    url = "%s/%s?portal_status_message=%s" % (url, redirect_to_template, psm)
    REQUEST.RESPONSE.redirect(url)
