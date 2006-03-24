# -*- coding: iso-8859-15 -*-
# Copyright (c) 2004-2005 Ministère de la justice <http://www.justice.gouv.fr/>
# Copyright (c) 2004-2005 Capgemini <http://capgemini.com>
# Copyright (c) 2004-2005 Nuxeo SARL <http://nuxeo.com>
# Author: Georges Racinet <gr@nuxeo.com>
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
#-------------------------------------------------------------------------------
# $Id$
""" CPSCourrier stack elements
"""
from Globals import InitializeClass

from Products.CPSWorkflow.stackregistries import WorkflowStackElementRegistry
from Products.CPSWorkflow.basicstackelements import UserStackElement
from Products.CPSWorkflow.basicstackelements import GroupStackElement

class CourrierUserStackElement(UserStackElement):
    """User Stack Element holding CPS Courrier Specific data
    """
    meta_type = 'Courrier User Stack Element'
    hidden_meta_type = 'Hidden Courrier User Stack Element'
    prefix = 'courrier_user'
    _allowed_attributes = ('delegation_date', 'directive', 'user_comment')

InitializeClass(CourrierUserStackElement)
WorkflowStackElementRegistry.register(CourrierUserStackElement)

class CourrierGroupStackElement(GroupStackElement):
    """Group Stack Element with CPS Courrier Specific data
    """
    meta_type = 'Courrier Group Stack Element'
    hidden_meta_type = 'Hidden Courrier Group Stack Element'
    prefix = 'courrier_group'
    _allowed_attributes = ('delegation_date', 'directive', 'user_comment')

InitializeClass(CourrierGroupStackElement)
WorkflowStackElementRegistry.register(CourrierGroupStackElement)
