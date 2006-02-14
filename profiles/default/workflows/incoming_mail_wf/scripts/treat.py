## Script (Python) "treat"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=state_change
##title=
##
proxy = state_change.object
msg_wftool = proxy.portal_messager_workflow
msg_wftool.treat(proxy)
