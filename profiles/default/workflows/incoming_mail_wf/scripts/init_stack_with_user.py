## Script (Python) "init_stack_with_user"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=state_change
##title=
##
from Products.CPSCourrier.workflows.scripts import init_stack_with_user
init_stack_with_user(state_change,
                     'Pilots', prefix='courrier_user',
                     directive='handle')
