## Script (Python) "bayes_learn_subject"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=state_change
##title=
##
from Products.CPSCourrier.workflows.scripts import bayes_learn_subject
bayes_learn_subject(state_change.object)
