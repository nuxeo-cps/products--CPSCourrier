## Script (Python) "flag_incoming_answered"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=state_change
##title=
##
from Products.CPSCourrier.workflows.scripts import flag_incoming_answered
flag_incoming_answered(state_change.object, sci_kw=state_change.kwargs)
