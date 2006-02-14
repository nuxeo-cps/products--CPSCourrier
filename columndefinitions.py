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

""" A simple tool that holds definitions of columns for tabular content. """

import os

from zope.interface import implements
from Globals import package_home
from AccessControl import ClassSecurityInfo
from OFS.Folder import Folder

from Products.PageTemplates.PageTemplateFile import PageTemplateFile

from Products.CMFCore.utils import UniqueObject, SimpleItemWithProperties
from Products.CMFCore.permissions import ManagePortal

from interfaces import IColumnDefinition, IColumnDefinitionsTool

_zmidir = os.path.join(package_home(globals()), 'zmi')

class ColumnDefinition(SimpleItemWithProperties):
    """ A definition of a display column.

    >>> ColumnDefinition()
    <ColumnDefinition at >
    """

    implements(IColumnDefinition)

    meta_type = 'CPS Column Definition'

    _properties = SimpleItemWithProperties._properties + (
        {'id': 'attribute', 'type' : 'string', 'mode' : 'w',
         'label' : 'attribute to lookup on displayed object'},
        {'id': 'href', 'type': 'string', 'mode': 'w',
         'label': 'Make a link out of the displayed object to this url'},
        {'id': 'label', 'type' : 'string', 'mode' : 'w',
         'label' : 'label for the whole column'},
        {'id': 'is_i18n', 'type': 'boolean', 'mode': 'w',
         'label': 'Label is i18n'},
        {'id': 'sortable', 'type': 'boolean', 'mode': 'w',
         'label': "Can this column's content be used for sorting"},
        )

    attribute = ''
    href = ''
    label = ''
    is_i18n = False
    is_sort_key = False

    def __init__(self, id, **kw):
        self._setId(id)
        self.manage_changeProperties(**kw)


class ColumnDefinitionsTool(UniqueObject, Folder):
    """Hold column definitions. """

    implements(IColumnDefinitionsTool)

    id = 'portal_columns'
    meta_type = 'CPS Column Definitions Tool'
    
    security = ClassSecurityInfo()

    #
    # ZMI
    #

    def all_meta_types(self):
        return( {'name' : 'CPS Column Definition',
                 'action' : 'manage_addColumnDefinitionForm',
                 'permission' : ManagePortal},
                )
    
    manage_addColumnDefinitionForm = PageTemplateFile('addColumnDefinition',
                                                      _zmidir)
 
    security.declareProtected(ManagePortal, 'manage_addColumnDefinition')
    def manage_addColumnDefinition(self, id=None, REQUEST=None):
        """ create an empty column definition

        >>> tool = ColumnDefinitionsTool()
        >>> tool.manage_addColumnDefinition(id='col')
        >>> tool.col
        <ColumnDefinition at portal_columns/>
        """
        
        if not id:
            return 'You have to specify an identifier!'
        ur = ColumnDefinition(id)
        self._setObject(id, ur)
        ur = self._getOb(id)
        if REQUEST is not None:
            REQUEST.RESPONSE.redirect(ur.absolute_url()+'/manage_workspace'
                                      '?manage_tabs_message=Added.')
