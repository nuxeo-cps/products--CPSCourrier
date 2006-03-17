##parameters=search_param=None, search_term=None
#$Id$
"""
Query the members or groups directories to select users or groups to assign
local roles.

This script is used by:
    - folder_localrole_form
    - forum_localrole_form (to be replaced by folder_localrole_form)
    - cps_chat_localroles_form (to be replaced by folder_localrole_form)
"""

from AccessControl import Unauthorized

#GR OVERLOAD FOR THIS COMMENT OUT
#if not context.portal_membership.canMemberChangeLocalRoles(context):
#    raise Unauthorized

# XXX backward compatibility: 'fullname' search is broken; use sn search instead
# http://svn.nuxeo.org/trac/pub/ticket/627
if search_param == 'fullname':
    search_param = 'sn'

results = []

if search_param in ('id', 'givenName', 'sn', 'email'):
    mdir = context.portal_directories.members
    id_field = mdir.id_field
    return_fields = (id_field, 'givenName', 'sn', 'email')
    if search_param == "id":
        search_param = id_field
    kwargs = {
        search_param: search_term,
        'return_fields': return_fields,
        }
    results = mdir.searchEntries(**kwargs)
    results.sort()

elif search_param == 'groupname':
    gdir  = context.portal_directories.groups
    # XXX hardcoded but not GroupsDirectory's job
    pseudo_groups = ['role:Anonymous', 'role:Authenticated']
    groups = []
    for pseudo_group in pseudo_groups:
        if pseudo_group.lower().find(search_term) != -1:
            groups.append(pseudo_group)
    results = gdir.searchEntries(**{gdir.id_field: search_term})
    results.extend(groups)

return results
