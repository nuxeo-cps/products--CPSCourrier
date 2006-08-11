##parameters=key=None
#$Id$

# This is to be called from a Select Widget on a mail document

# XXX how to get cleany rid of hardcoded directory name ?
ldir = context.portal_directories['local_addressbook']
title_field = ldir.title_field

# Context is then supposed to
# be the proxy that the datamodel was made from, ie the mailbox in case of
# creation or the mail in case of edition/view

if context.portal_type == 'Mailbox':
    mailbox = context
else:
    mailbox = context.aq_inner.aq_parent

mbox_ptype = getattr(mailbox, 'portal_type', None)
if mbox_ptype != 'Mailbox':
    raise ValueError(mbox_ptype)

query = {'ou': mailbox.getDocid()}

if key is not None:
    query['local_id'] = key
    entry_ids = ldir.searchEntries(**query)
    return entry_ids and ldir.getEntry(entry_ids[0])[title_field] or None

# return_fields don't go through read_expr, and entry title field is typically
# a fullname...
entry_ids = ldir.searchEntries(**query)
return [(e_id, ldir.getEntry(e_id)[title_field]) for e_id in entry_ids]







