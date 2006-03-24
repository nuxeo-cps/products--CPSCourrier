# Copyright (c) 2004-2005 Ministère de la justice <http://www.justice.gouv.fr/>
# Copyright (c) 2004-2005 Capgemini <http://capgemini.com>
# Copyright (c) 2004-2005 Nuxeo SARL <http://nuxeo.com>
# Author: Anahide Tchertchian <at@nuxeo.com>
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

from Products.CPSWorkflow.interfaces import IStackElement
from Products.CPSWorkflow.interfaces import IHierarchicalWorkflowStack

class IStackElementWithData(IStackElement):
    """Stack Element With Data.

    A stack element that can hold a mapping and implements default read and
    write values.
    """

class ICourrierStack(IHierarchicalWorkflowStack):
    """ A hierarchical stack that can hold IStackElementWithData instances."""




