# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
# Author: G. Racinet <gracinet@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
# $Id$

from Products.CMFCore.utils import getToolByName

from localrolesview import LocalRolesView

class RoadmapView(LocalRolesView):

    stack_var_id = 'Pilots'

    def __init__(self, *args):
        LocalRolesView.__init__(self, *args)

        self.wftool = getToolByName(self.context, 'portal_workflow')
        self.stack = self.wftool.getStackFor(self.context, self.stack_var_id)

    def canDoAction(self, transition_id):
        wfs = getattr(self, 'wfs', None)
        if wfs is None:
            wfs = self.wfs = self.wftool.getWorkflowsFor(self.context)

        for wf in wfs:
            if wf.isActionSupported(self.context, transition_id):
                return True
        return False

    def canMoveDown(self):
        return self.canDoAction('move_down_delegatees')

    def canManage(self):
        return self.canDoAction('manage_delegatees')

    def renderStack(self, mode):
        return self.stack.render(context=self.context, mode=mode)

    def renderUsersLayout(self):
        return self.renderLayout(name='roadmap_users_search')['rendered']

    def renderGroupsLayout(self):
        return self.renderLayout(name='roadmap_groups_search')['rendered']
