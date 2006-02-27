##parameters=key=None, **kw
#$Id$
"""Return a portal type vocabulary, used as MethodVocabulary."""

# just because one cannot add empty value for static vocabularies
# (these thing should be handled by Select Widget, not the voc  anyway.

basevoc = context.portal_vocabularies['subject_voc']
if key is None:
    return basevoc.items()
return basevoc.getMsgid(key)
