## Script (Python) "unlock_locked_before_abandon"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=state_change
##title=
##
return state_change.object.content_unlock_locked_before_abandon(state_change)
