##parameters=current_var_id, search_param=None, search_term=None
#$Id$
"""
Perform search for members/groups that will be put in stacks

Changes wrt folder_localrole_search script in CPSDefault:
- perform security check on stack, and not on the 'Change permissions'
  permission

"""

from AccessControl import Unauthorized

if not context.portal_workflow.canManageStack(context, current_var_id):
    raise Unauthorized

if search_param in ('fullname', 'email'):
    mdir = context.portal_directories.members
    id_field = mdir.id_field
    # first get portal member ids without externall call (e.g. LDAP)
    return_fields = (id_field, 'givenName', 'sn', 'email')
    results = {}
    if search_param == 'fullname':
        # XXX cannot search both parameters at the same time because we want a
        # OR search, not AND.
        from_ids = mdir.searchEntries(**{id_field: search_term,
                                         'return_fields': return_fields})
        from_fullnames = mdir.searchEntries(fullname=search_term,
                                            return_fields=return_fields)
        for id, values in (from_ids + from_fullnames):
            results[id] = values
        results = results.items()
    elif search_param == 'email':
        results = mdir.searchEntries(email=search_term,
                                     return_fields=return_fields)
    results.sort()
elif search_param == 'groupname':
    gdir  = context.portal_directories.groups
    # XXX hardcoded but not GroupsDirectory's job
    pseudo_groups = ['role:Anonymous', 'role:Authenticated']
    groups = []
    for pseudo_group in pseudo_groups:
        if pseudo_group.lower().find(search_term) != -1:
            groups.append(pseudo_group)
    groups.extend(gdir.searchEntries(group=search_term))
    results = groups

return results
