## Script (Python) "mark_incoming_mail_as_answered"
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

# see if a transition needs to be performed by incoming mail
msg_wftool.markIncomingMailAsAnswered(proxy)
