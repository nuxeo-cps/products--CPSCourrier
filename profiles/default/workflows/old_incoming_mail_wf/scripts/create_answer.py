## Script (Python) "create_answer"
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
msg_wftool.createAnswerOf(proxy, proxy.aq_inner.aq_parent)
