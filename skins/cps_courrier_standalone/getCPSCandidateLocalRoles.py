##parameters=
# $Id$
root_roles = {'mailboxes': ('LocalManager',
                            'Supervisor',
                            'Contributor',
                            ),
              'mail_templates': ('SectionManager',
                                 'SectionReviewer',
                                     'SectionReader',
                                 ),
              'help_center': ('WorkspaceManager',
                              'WorkspaceMember',
                              'WorkspaceReader',
                                 ),
              }
utool = context.portal_url
root = utool.getRpath(context).split('/')[0]

roles = root_roles.get(root)
if roles is not None:
    return roles

#Fallback
return context.portal_membership.getCPSCandidateLocalRoles(context)
