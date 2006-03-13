# -*- coding: iso-8859-15 -*-
# Copyright (c) 2004-2005 Minist�re de la justice <http://www.justice.gouv.fr/>
# Copyright (c) 2004-2005 Capgemini <http://capgemini.com>
# Copyright (c) 2004-2005 Nuxeo SAS <http://nuxeo.com>
# Authors: Anahide Tchertchian <at@nuxeo.com>
#          Georges Racinet <gr@nuxeo.com>
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
"""CPSCourrier Stacks
"""

from zLOG import LOG, DEBUG
from zope.interface import implements

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from DateTime import DateTime

from Products.CMFCore.utils import getToolByName

from Products.CPSWorkflow.basicstacks import HierarchicalStack
from Products.CPSWorkflow.stackregistries import WorkflowStackRegistry

from Products.CPSCourrier.interfaces import IStackElementWithData
from Products.CPSCourrier.interfaces import IHierarchicalStackWithData


###########################################################
###########################################################

class HierarchicalStackWithData(HierarchicalStack):
    """A hierarchical stack whose elements implement StackElementWithData

    """

    meta_type = 'Hierarchical Stack With Data'

    security = ClassSecurityInfo()
    security.declareObjectPublic()

    implements(IHierarchicalStackWithData)

    render_method = 'stack_hierarchical_data_render'

    #
    # Overload
    #

    def push(self, elt=None, level=None, **kw):
        """Push elements taking care of other data
        """
        # required
        push_ids = kw.get('push_ids', ())

        # called with bare push_ids
        if not push_ids:
            return

        levels = kw.get('levels', ())

        # compat with standard stack management screens
        if not levels:
            level = self.getCurrentLevel()
            levels = len(push_ids) * [level]

        # optional data
        # XXX we get a pack of lists because that's what comes from
        # HTTP request. Let a view take care of this ?
        data_lists = dict( (key, kw.get(key))
                           for key in kw.get('data_lists', ()))

        # Push elements;
        # takes insertion between two existing levels into account
        for i, push_id in enumerate(push_ids):
            elt_info = {}

            # check level
            level = levels[i]
            if isinstance(level, int):
                # ok
                pass
            elif isinstance(level, str):
                try:
                    level = int(level)
                except ValueError:
                    # convention to insert the level itself
                    # see HierarchicalStack._push
                    split = level.split('_')
                    try:
                        elt_info['low_level'] = int(split[0])
                        elt_info['high_level'] = int(split[1])
                    except (IndexError, ValueError):
                        # Wrong user input
                        LOG("HierarchicalStackWithData.push", DEBUG,
                            "wrong user input, level split=%s"%(level,))
                        continue
            else:
                # wrong user input
                LOG("HierarchicalStackWithData.push", DEBUG,
                    "wrong user input, level=%s"%(level,))
                #print "wrong user input, level=%s"%(level,)
                continue

            # optional data
            for key, item in data_lists.items():
                try:
                    elt_info[key] = item[i]
                except IndexError:
                    pass

            self._push(push_id, level=level, **elt_info)


    # XXX TODO (finalization):
    # check that all overloads below are still necessary
    def hasUpperLevel(self):
        """Has the stack a non empty level upper than current level
        """
        level = self.getUpperLevel()
        res = (level is not None)
        return res

    def getUpperLevel(self):
        """Get existing upper level
        """
        current_level = self.getCurrentLevel()
        upper_levels = [x for x in self.getAllLevels()
                        if x > current_level]
        level = None
        if len(upper_levels)>0:
            level = upper_levels[0]
        return level

    def hasLowerLevel(self):
        """Has the stack a non empty level lower than the current level
        """
        level = self.getLowerLevel()
        res = (level is not None)
        return res

    def getLowerLevel(self):
        """Get existing lower level
        """
        current_level = self.getCurrentLevel()
        lower_levels = [x for x in self.getAllLevels()
                        if x < current_level]
        level =  None
        if len(lower_levels)>0:
            level = lower_levels[-1]
        return level

    def doIncLevel(self, date=None):
        """Increment the level value

        The level has to exist and host elts

        """
        new_level = self.getUpperLevel()
        if new_level is not None:
            self.setCurrentLevel(new_level)
        return self._level

    def doDecLevel(self, date=None):
        """Decrement the level value

        The level has to exist and host elts

        """
        new_level = self.getLowerLevel()
        if new_level is not None:
            self.setCurrentLevel(new_level)
        return self._level

    def reset(self, **kw):
        """Reset the stack

        new_stack     : stack that might be a substitute of self
        reset_ids     : new elements to add at current level, but will need poles
                        and stuff so dont use it.
        current_level : new level to set n stack (new level is ot taken from
                        the new stack)
        """
        HierarchicalStack.reset(self, **kw)

        # set the level
        level = kw.get('current_level')
        if level is not None:
            self.setCurrentLevel(level)

        return self

    def setCurrentLevel(self, level):
        """Set current level

        Level has to hold elements
        """
        if level in self.getAllLevels():
            self._level = level
        return self._level

    def cutBelowCurrentLevel(self):
        """Remove elements below current level
        """
        current_level = self.getCurrentLevel()
        for level in self.getAllLevels():
            if level < current_level:
                self._getElementsContainer()[level] = []

    def cutAboveCurrentLevel(self):
        """Remove elements above current level
        """
        current_level = self.getCurrentLevel()
        for level in self.getAllLevels():
            if level > current_level:
                self._getElementsContainer()[level] = []


    #
    # Specific helper methods
    #

    def getLevelAndIndexFor(self, elt_id, level=None, all=False):
        """Get the level and index for the given stack element id.

        If level is None, search for the element in all levels and return the
        first one found.

        If all is True, return a list of all levels and indexes where user or
        one of his groups is found.

        If not found, return None.

        Used when creating the answer to set the new level on the given stack,
        for acknoledgment/treatment actions, and for resynchronization.
        """
        if all:
            # get list of all results
            res = []
            if level is not None:
                index = self._getStackElementIndex(elt_id, level)
                if index != -1:
                    res.append((level, index))
            else:
                all_levels = self.getAllLevels()
                for level in all_levels:
                    index = self._getStackElementIndex(elt_id, level)
                    if index != -1:
                        res.append((level, index))
            return res
        else:
            if level is not None:
                index = self._getStackElementIndex(elt_id, level)
                if index != -1:
                    return (level, index)
            else:
                all_levels = self.getAllLevels()
                for level in all_levels:
                    index = self._getStackElementIndex(elt_id, level)
                    if index != -1:
                        return (level, index)
            return None

    def setEditableAttributes(self, edit_ids, data_lists):
        """Set editable attributes on all given elements with given values.

        edit_ids follow the pop_ids convention
        ('level,prefixed_stack_element_id').

        """
        for i, edit_id in enumerate(edit_ids):
            split = edit_id.split(',')
            level = int(split[0])
            the_id = split[1]
            index = self._getStackElementIndex(the_id, level)
            if index != -1:
                elt = self._elements_container[level][index]
                if IStackElementWithData.providedBy(elt):
                    for key, data_list in data_lists.items():
                        elt[key] = data_list[i]
                # used to be a try: except IndexError around all this.

    #
    # rendering
    #

    def getStackContentForRender(self, context, mode='view', **kw):
        """Return levels and dictionnary used in templates that display the
        stack with levels as keys

        Assume stack is a HierarchicalStackWithData storing

        context is passed to be able to get portal tools.
        mode can either be 'view', 'edit' or insert'.
        wftype can be passed in kw is either 'incoming', 'outgoing' or None. If
        not None, information about preselected level is added to the stack
        rendering.
        """

        # help to define stack content to display
        dirtool = getToolByName(context, 'portal_directories')
        aclu = context.acl_users
        assert(aclu.meta_type == 'CPS User Folder')
        members_dir = getattr(dirtool, aclu.users_dir)
        groups_dir = getattr(dirtool, aclu.groups_dir)
        cpsmcat = context.translation_service
        kwargs = {
            # for members
            'members': members_dir,
            'groups': groups_dir,
            'cpsmcat': cpsmcat,
            'date_format': cpsmcat('cpscourrier_date_format').encode(
                          'iso-8859-15'),
            }

        infos = {}
        stack_content = self.getStackContent(type='object', context=context)
        current_level = self.getCurrentLevel()
        # stack content is a dictionnary with levels as keys and lists of
        # delegatees as values
        #LOG("getStackContentForRender", DEBUG, "items=%s"%(stack_content,))

        # XXX GR used to be call to a specific tool in edit mode to know
        # which element refers to the member currently managing the stack,
        # to forbid deletion. This will be done at the element level instead

        all_levels = self.getAllLevels()

        for level in all_levels:
            level_content = stack_content[level]
            level_items = []
            # fill level items
            for index, elt in enumerate(level_content):
                elt_infos = self.getStackElementForRender(elt, level,
                                                          mode, **kwargs)
                # protect delegatee self-deletion by adding a 'deletable'
                # info in edit mode
                if mode == 'edit' and level == current_level:
                    elt_infos['deletable'] = not elt.holdsCurrentMember(context)
                level_items.append(elt_infos)
            infos[level] = {
                'level_str': str(level),
                'label_level': 'level' + str(level),
                'current_level': (level == current_level),
                'items': level_items,
                }

        # special levels for insert mode (e.g empty or intermediate levels)
        if mode == 'insert':
            # get new levels, e.g empty levels between non empty levels, and
            # intermediate levels, e.g intermediate levels between non empty
            # levels...
            all_levels = self.getAllLevels()
            all_insert_levels = self.getInsertLevels(all_levels)

            for level in all_insert_levels:
                # all insert levels are insertable
                insertable = 1
                # set preselection
                preselected = False
                if level not in all_levels:
                    # info for empty levels
                    infos[level] = {
                        'level_str': str(level),
                        'label_level': 'level' + str(level),
                        'current_level': False,
                        'items': [],
                        'insertable': insertable,
                        'preselected': preselected,
                        }
                else:
                    # infos[level] is already set above
                    infos[level]['insertable'] = insertable
                    infos[level]['preselected'] = preselected
            levels = all_insert_levels
        else:
            levels = infos.keys()
            levels.sort()

        #LOG("getStackContentForRender", DEBUG,
        #    "res for mode %s=%s"%(mode, levels))

        levels.reverse()

        #LOG("getStackContentForRender", DEBUG,
        #    "res for mode %s=(%s, %s, %s)"%(mode, levels, infos.keys(), infos))

        return (levels, infos)


    def getStackElementForRender(self, elt, level, mode, **kw):
        """ Get info about a stack element for rendering. """

        # basic kws
        infos = elt()

        # dates

        date_fmt = kw.get('date_format', '%Y/%m/%d')
        for key, value in infos.items():
            if isinstance(value, DateTime):
                date_str = value.strftime(date_fmt)
                infos[key +  '_str'] = date_str

        elt_id = elt.getId()

        # for <input> tags
        infos.update({
            'input_id': str(level) + ',' + elt_id,
            'label_id': 'label_' + str(level) + ',' + elt_id,
            })

        # user/group info
        cpsdir = None
        if elt_id.startswith('user'):
            user = True
            cpsdir = kw.get('members')
        elif elt_id.startswith('group'):
            group = True
            cpsdir = kw.get('group')
        if not cpsdir: # happens, e.g, in unit tests
            return infos

        id_wo_prefix = elt.getIdWithoutPrefix()
        entry = None
        if id_wo_prefix:
            entry = cpsdir.getEntry(id_wo_prefix, default=None)
        if entry is None:
            # not found
            infos['identite'] = id_wo_prefix
        else:
            title = entry.get(cpsdir.title_field, '')
            if not title:
                title = id_wo_prefix
            if not user:
                # translate group title
                cpsmcat = kw.get('cpsmcat')
                title = cpsmcat(title, default=title)
            infos['identite'] = title

        return infos

    def getInsertLevels(self, all_levels):
        """Helper method to find intermediate and empty levels in stacks,

        Returns a list of integers and strings that represent the list of
        levels where delegatees can be inserted.
        """
        res = []
        all_levels.sort()

        if len(all_levels) == 0:
            res.append(0)
        else:
            # extremes
            start = all_levels[0] - 1
            res.append(start)

            # find all consecutive integers in this list
            # init with two first elements
            index = 0
            current = all_levels[index]
            while index < len(all_levels) - 1:
                res.append(current)
                index += 1
                next = all_levels[index]
                #LOG("getIntermediateLevels", DEBUG,
                #    "current=%s, next=%s"%(current, next))
                #print "current=%s, next=%s"%(current, next)
                if (current + 1 == next):
                    # add intermediate level
                    res.append(str(current) + '_' + str(next))
                else:
                    # - add only one missing level
                    missing_level = current + 1
                    res.append(missing_level)
                current = next
            res.append(current)

            end = all_levels[-1] + 1
            res.append(end)

        #print "results"
        #print "all_levels=%s, res=%s"%(all_levels, res)
        #LOG("getIntermediateLevels", DEBUG,
        #    "all_levels=%s, res=%s"%(all_levels, res))

        return res


InitializeClass(HierarchicalStackWithData)

#####################################################################
#####################################################################

WorkflowStackRegistry.register(HierarchicalStackWithData)