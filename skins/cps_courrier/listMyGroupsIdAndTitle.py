##parameters=REQUEST=None

aclu = context.acl_users
dtool = context.portal_directories

me = context.portal_membership.getAuthenticatedMember()
uid = me.getMemberId()

groups_dir = dtool[aclu.groups_dir]
return_fields = [groups_dir.id_field, groups_dir.title_field]
query = {aclu.groups_members_field: uid}
res = groups_dir.searchEntries(return_fields=return_fields, **query)

return [('', '')] + [tuple(info[f] for f in return_fields) for _, info in res]
