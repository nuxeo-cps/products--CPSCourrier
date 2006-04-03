##parameters=workflow_action, REQUEST=None, do_redirect=True, **kw
# $Id$
""" Handle the doActionFor for the given transition id + the redirect

CPSCourrier: added an explicit do_redirect flag
XXX: This should be merged back to CPSDefault@trunk once it's not frozen any
longer
"""

wftool = context.portal_workflow

if REQUEST is not None:
    kw.update(REQUEST.form)

comments = kw.get('comments', '')

folder = context.aq_parent
id = context.getId()
url = None

psm = 'psm_status_changed'

if workflow_action != 'copy_submit':
    # accept, reject, ...
    if comments:
        del kw['comments']
    kw['comment'] = comments
    res = wftool.doActionFor(context, workflow_action, **kw)
    if same_type(res, ()):
        if res[0] == 'ObjectMoved':
            rpath = res[1]
            url = context.portal_url()
            if not url.endswith('/'):
                url += '/'
            url += rpath
else:
    # No section has been specified
    # XXX We should get a list in here
    if REQUEST and len(REQUEST.form) < 3:
        psm = 'psm_you_must_select_sections_for_publishing'

    # publishing: copy and initalize proxy into one or more sections
    allowed_transitions = wftool.getAllowedPublishingTransitions(context)
    for transition in allowed_transitions:
        rpaths = kw.get(transition)
        if rpaths:
            if same_type(rpaths, ''):
                rpaths = (rpaths,)
            for rpath in rpaths:
                wftool.doActionFor(context, workflow_action,
                                   dest_container=rpath,
                                   initial_transition=transition,
                                   comment=comments)

if REQUEST is not None and do_redirect:
    # If the object has been deleted, we can't redirect to it.
    if url is None:
        if id in folder.objectIds():
            url = context.absolute_url()
        else:
            url = folder.absolute_url()

    if psm == 'psm_you_must_select_sections_for_publishing':
        redirect_url = '%s/content_submit_form?%s' % (
            url, 'portal_status_message=%s'%psm)
    else:
        redirect_url = '%s/?%s' % (url, 'portal_status_message=%s'%psm)
    REQUEST.RESPONSE.redirect(redirect_url)
