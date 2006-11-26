##parameters=key=None, **kw
#$Id$
"""Empty key Method Vocab. Remove and use widget-level empty_key."""

basevoc = context.portal_vocabularies['mail_priority']
if key is None:
    return basevoc.items()
return basevoc.getMsgid(key)
