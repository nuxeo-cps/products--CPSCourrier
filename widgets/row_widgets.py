# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
# Author: Georges Racinet <gracinet@nuxeo.com>
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
#
# $Id$

"""CPSCourrier specific row widgets
"""

from logging import getLogger

from Globals import InitializeClass

from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.Widget import widgetRegistry
from Products.CPSDashboards.widgets.row_widgets import CPSMultiBooleanWidget

from Products.CPSCourrier.config import STACK_ID

logger = getLogger('CPSCourrier.row_widgets')

class CPSCourrierToDoRowWidget(CPSMultiBooleanWidget):
    """Evaluates booleans for high-level actions in one shot.

    Reason: performance, workflow queries can be costly
    Conventions are like those of CPSMultiBooleanWidget
    Fields are ignored

    This is equivalence with a Multi Boolean working on following booleans
    (in that order):
      - to process: user is in the roadmap at current level
      - to watch: user is in the roadmap
      - to handle: incoming mail state is 'received'

    Therefore this widget is pin-compatible with implementations based on
    brains methods
    """

    meta_type = "Courrier To Do Row Widget"

    def prepare(self, datastructure, **kw):
        default = self.displayed_values[-1]
        wid = self.getWidgetId()

        dm = datastructure.getDataModel()
        proxy = dm.getProxy()
        if proxy is None:
            datastructure[wid] = default
            return

        wftool = getToolByName(self, 'portal_workflow')

        # state based criteria
        state = wftool.getInfoFor(proxy, 'review_state')
        if state == 'received':
            datastructure[wid] = self.displayed_values[2]
            return

        if state in ['trash', 'sent', 'closed', 'locked']:
            datastructure[wid] = default
            return

        # stack based criteria
        stack = wftool.getStackFor(proxy, STACK_ID)
        if stack is None:
            datastructure[wid] = default
            return

        mtool = getToolByName(self, 'portal_membership')
        user = mtool.getAuthenticatedMember()
        user_id = user.getId()

        # To process: user is pilot
        clevel = stack.getCurrentLevel()
        pilots = [x.getIdForRoleSettings() for x in stack._getManagers()
                  if x is not None]
        logger.debug("Stack Managers => %s" % pilots)

        if user_id in pilots:
            datastructure[wid] = self.displayed_values[0]
            return

        user_gids = set('group:%s' % gid for gid in user.getGroups())
        if user_gids.intersection(pilots):
            datastructure[wid] = self.displayed_values[0]
            return

        # To watch: user is in the stack
        delegatees = set()
        for level in stack.getAllLevels():
            delegatees.update(x for x in stack.getStackContent(type='role',
                                                               context=proxy)[level])
        logger.debug("delegatees: %s", delegatees)
        user_gids.add(user_id)
        if delegatees.intersection(user_gids):
            datastructure[wid] = self.displayed_values[1]
            return

        datastructure[wid] = default

InitializeClass(CPSCourrierToDoRowWidget)
widgetRegistry.register(CPSCourrierToDoRowWidget)
