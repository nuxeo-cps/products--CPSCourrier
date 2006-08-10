## Script (Python) "dispatch_after_create"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=state_change
##title=
##
from Products.CPSCourrier.workflows.scripts import bayes_guess_subject
from Products.CPSCourrier.workflows.scripts import paper_auto_handle

proxy = state_change.object
if proxy.portal_type.endswith('Email'):
    bayes_guess_subject(state_change.object)
elif not state_change.kwargs.get('no_handle'):
    # no_handle is used in automated tests
    paper_auto_handle(proxy)
