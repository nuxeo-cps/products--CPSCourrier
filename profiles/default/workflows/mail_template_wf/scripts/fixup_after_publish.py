## Script (Python) "fixup_after_publish"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=state_change
##title=
##
from Products.CPSWorkflow.util import updateEffectiveDate
return updateEffectiveDate(state_change.object)
