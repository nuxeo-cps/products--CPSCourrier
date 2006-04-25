## Script (Python) "delete_language_from_proxy"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=state_change
##title=
##
lang=state_change.kwargs.get('lang')
state_change.object.delLanguageFromProxy(lang)
