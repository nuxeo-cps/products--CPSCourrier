# Copyright (c) 2006 Nuxeo SAS <http://nuxeo.com>
# Author : Georges Racinet <gracinet@nuxeo.com>
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

from Globals import InitializeClass

from Products.CPSWorkflow.stackregistries import WorkflowStackElementRegistry
from Products.CPSWorkflow.stackelement import StackElement

class ExampleStackElement(StackElement):
     meta_type = 'Example Stack Element'
     hidden_meta_type = 'Hidden Example Stack Element'
     prefix = 'example'
     _allowed_attributes = ('date', 'comment','d1', 'd2')

WorkflowStackElementRegistry.register(ExampleStackElement)
