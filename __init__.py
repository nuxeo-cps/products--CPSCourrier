# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
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
"""Initialise the extension profile for the CPSCourrier product"""

from AccessControl import ModuleSecurityInfo

from Products.GenericSetup import profile_registry
from Products.GenericSetup import EXTENSION
from Products.CMFCore.DirectoryView import registerDirectory
from Products.CPSCore.interfaces import ICPSSite

# temporary fix for a bug in CPSCore events
import PatchCPSCoreCPSTypes

# various registrations are done therein
import widgets, workflows

# Module security for workflow scripts
ModuleSecurityInfo('Products.CPSCourrier.workflows.scripts').declarePublic(
    'reply_to_incoming')
ModuleSecurityInfo('Products.CPSCourrier.workflows.scripts').declarePublic(
    'flag_incoming_answered')
ModuleSecurityInfo('Products.CPSCourrier.workflows.scripts').declarePublic(
    'flag_incoming_handled')
ModuleSecurityInfo('Products.CPSCourrier.workflows.scripts').declarePublic(
    'init_stack_with_user')
ModuleSecurityInfo('Products.CPSCourrier.workflows.scripts').declarePublic(
    'send_reply')
ModuleSecurityInfo('Products.CPSCourrier.workflows.scripts').declarePublic(
    'compute_reply_body')



# Stack API
ModuleSecurityInfo('Products.CPSCourrier.workflows.scripts').declarePublic(
    'init_stack_with_user')

# Relations API
ModuleSecurityInfo('Products.CPSCourrier.relations').declarePublic(
    'get_thread_for')

registerDirectory('skins', globals())

def initialize(registrar):
    # Extension profile registration
    profile_registry.registerProfile(
        'default',
        'CPS Courrier',
        "Mail tracking and management system for CPS",
        'profiles/default',
        'CPSCourrier',
        EXTENSION,
        for_=ICPSSite)
