##parameters=key=None
#$Id$

# This is to be called from a Select Widget on a mail document
# behavior if key is not None has nothing special. The real point is to list
# relevant entries if key is None 

# XXX how to get cleany rid of hardcoded directory name ?
dtool = context.portal_directories
ldir = dtool['local_addressbook']
title_field = ldir.title_field

# Context is then supposed to
# be the proxy that the datamodel was made from, ie the mailbox in case of
# creation or the mail in case of edition/view

if context.portal_type == 'Mailbox':
    mailbox = context
elif hasattr(context.aq_explicit, 'getRID'):
    #GR Shame on me this is a brain. We are called from a row layout on a
    # Catalog Tabular Widget. Cannot avoid this for now, do the costly thing
    # getObject doesn't even work.
    utool = context.portal_url
    path = context.relative_path.split('/')[:-1]
    mailbox = utool.getPortalObject().restrictedTraverse(path)
else:
    mailbox = context.aq_inner.aq_parent

mbox_ptype = getattr(mailbox, 'portal_type', None)
if mbox_ptype != 'Mailbox':
    raise ValueError(mbox_ptype)

if key is not None:
    # this directory ids have the form local_id, ou
    # add sanity check ?
    return ldir.getEntry(key)[title_field]

# return_fields don't go through read_expr, and entry title field is typically
# a fullname...

ou =  mailbox.getContent().getDataModel()['ou']

if dtool.hasObject('local_addressbook_ldap'):
    query = {'dn': '*,ou=%s,*'}
else:
    query = {'mailbox': ou}

entry_ids = ldir.searchEntries(**query)
items = [(e_id, ldir.getEntry(e_id)[title_field]) for e_id in entry_ids]
return items

items.insert(0, ('', ''))

return items






