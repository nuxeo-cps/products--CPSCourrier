## Script (Python) "add_language_to_proxy"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=state_change
##title=
##
lang=state_change.kwargs.get('lang')
from_lang=state_change.kwargs.get('from_lang')
state_change.object.addLanguageToProxy(lang, from_lang)
