## Script (Python) "forward_mail"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=state_change
##title=
##
from Products.CPSCourrier.workflows.scripts import forward_mail
mto = state_change.kwargs.get('target_emailaddress')
comment = state_change.kwargs.get('comments', '')
forward_mail(state_change.object, mto, comment)
