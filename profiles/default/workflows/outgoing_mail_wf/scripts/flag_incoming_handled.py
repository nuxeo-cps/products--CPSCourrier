## Script (Python) "flag_incoming_answered"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=state_change
##title=
##
from Products.CPSCourrier.workflows.scripts import flag_incoming_handled
flag_incoming_handled(state_change.object)
