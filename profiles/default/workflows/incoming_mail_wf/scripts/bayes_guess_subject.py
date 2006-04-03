## Script (Python) "bayes_guess_subject"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=state_change
##title=
##
from Products.CPSCourrier.workflows.scripts import bayes_guess_subject
bayes_guess_subject(state_change.object)
