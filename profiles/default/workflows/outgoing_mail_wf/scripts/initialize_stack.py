## Script (Python) "initialize_stack"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=state_change
##title=
##
proxy = state_change.object

# initialize stack
msg_wftool = proxy.portal_messager_workflow
msg_wftool.initializeStack(proxy)
