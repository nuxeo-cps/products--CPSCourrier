# -*- coding: iso-8859-15 -*-
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
#-------------------------------------------------------------------------------
# $Id$
""" Stack Elements With Data

These stack elements store metadata besides user or group information. These
metadata aren't based on a schema. They come with a system for default values
and can be accessed via the dict API.
"""

from copy import deepcopy

from zLOG import LOG, DEBUG
from zope.interface import implements

from DateTime import DateTime

from Globals import InitializeClass
from Acquisition import aq_base
from ZODB.PersistentMapping import PersistentMapping

from Products.CPSWorkflow.stackregistries import WorkflowStackElementRegistry
from Products.CPSWorkflow.stackelement import StackElement

from Products.CPSCourrier.interfaces import IStackElementWithData

_missing = object()

class StackElementWithData(StackElement, PersistentMapping):
    """Stack Element With Data
    """
    meta_type = 'Stack Element With Data'

    implements(IStackElementWithData)

    # keys that have default values, and a callable
    # or method id to compute it
    _default_reads = {'id' : 'getId',
                      'id_without_prefix' : 'getIdWithoutPrefix',
                      'id_for_role_settings' : 'getIdWithoutPrefix'}

    # same thing for writes. Does not override existing data.
    # typical use-case: initial date
    _default_writes = {'delegation_date' : DateTime}

    def __init__(self, id, **kw):
        self._setId(id)
        PersistentMapping.__init__(self, **kw)
        ## Already import default_writes ?

    def applyDefault(self, key, how):
        return callable(how) and how() or getattr(aq_base(self), how)()

    def __call__(self):
        info_dict = dict(self)
        info_dict.update((key, self.applyDefault(key, how))
                         for key, how in self._default_reads.items()
                         if not key in info_dict
                         )

        return info_dict

    def __str__(self):
        info_str = "<StackElementWithData %s >" %(self(),)
        return info_str

    def __getitem__(self, key):
        if not key in self:
            return self.applyDefault(key, self._default_reads[key])
        else:
            return PersistentMapping.__getitem__(self, key)

    def __setitem__(self, key, value):
        if value is None:
            how = self._default_writes.get(key)
            if how is not None:
                value = self.applyDefault(key, how)
        PersistentMapping.__setitem__(self, key, value)

    def update(self, data):
        PersistentMapping.update(self, data)
        PersistentMapping.update(self,
                                 ((key, self.applyDefault(key, how))
                                  for key, how in self._default_writes.items()
                                  if not key in self))


class UserStackElementWithData(StackElementWithData):
    """User Stack Element With Data
    """
    meta_type = 'User Stack Element With Data'
    hidden_meta_type = 'Hidden User Stack Element'
    prefix = 'user_wdata'

InitializeClass(UserStackElementWithData)


class GroupStackElementWithData(StackElementWithData):
    """User Stack Element With Data
    """
    meta_type = 'User Stack Element With Data'
    hidden_meta_type = 'Hidden Group Stack Element'
    prefix = 'group_wdata'


    def getIdForRoleSettings(self):
        # set the 'group:' prefix for role settings
        role_id = 'group:' + self.getIdWithoutPrefix()
        return role_id

    _default_writes = StackElementWithData._default_writes.copy()
    _default_writes['id_for_role_settings'] =  'getIdForRoleSettings'


InitializeClass(GroupStackElementWithData)


##########################################################
##########################################################

WorkflowStackElementRegistry.register(UserStackElementWithData)
WorkflowStackElementRegistry.register(GroupStackElementWithData)
