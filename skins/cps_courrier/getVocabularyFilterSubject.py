##parameters=key=None, **kw
#$Id$
"""Subject voc with empty key.

# just because one cannot add empty value for static vocabularies
# (these things can now be handled by Select Widget)."""

basevoc = context.portal_vocabularies['subject_voc']
if key is None:
    return basevoc.items()
return basevoc.getMsgid(key)
