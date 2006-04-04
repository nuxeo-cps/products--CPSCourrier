## Script (Python) "reply_to_incoming"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=state_change
##title=
##
from Products.CPSCourrier.workflows.scripts import reply_to_incoming
base_reply_rpath = state_change.kwargs.get('base_reply_rpath', '')
outgoing_proxy = reply_to_incoming(state_change.object,
                                   base_reply_rpath=base_reply_rpath)
url = "%s/cpsdocument_edit_form" % outgoing_proxy.absolute_url()
context.REQUEST.RESPONSE.redirect(url)
