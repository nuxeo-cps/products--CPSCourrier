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

"""Directory MultiId Widget
"""
from Globals import InitializeClass
from Acquisition import aq_parent, aq_inner

from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.Widget import widgetRegistry
from Products.CPSSchemas.Widget import CPSWidget
from Products.CPSSchemas.BasicWidgets import renderHtmlTag
from Products.CPSSchemas.BasicWidgets import CPSProgrammerCompoundWidget


class CPSDirectoryMultiIdWidget(CPSProgrammerCompoundWidget):
    """A widget that makes ids from multiple sources.

    The first field is the target field, it gets composed from the other
    ones, that are in principle managed by subwidgets"""

    meta_type = "Directory Multi Id Widget"
    _properties = CPSProgrammerCompoundWidget._properties + (
        {'id': 'ldap_syntax', 'type': 'boolean', 'mode': 'w',
         'label': 'Use ldap dn syntax?'},
        )

    ldap_syntax = False
    render_method = 'widget_directory_multi_id_render'

    def _getPrepareValidateMethod(self):
        """Override. Called from CPSProgrammerCompondWidget."""
        return self.prepare_validate

    def prepare_validate(self, action, datastructure):
        """prepare or validate datastructure."""

        if action in ['prepare', 'prevalidate']:
            return
        elif action != 'validate':
            raise ValueError(action)

        dm = datastructure.getDataModel()
        id_field = self.fields[0]
        layout = aq_parent(aq_inner(self))
        subfields = self.fields[1:]
        if self.ldap_syntax:
            items = ['%s=%s' % (field_id, dm[field_id])
                     for field_id in subfields]
        else:
            items = [dm[field_id] for field_id in subfields]

        dm[self.fields[0]] = ','.join(items)
        return True


InitializeClass(CPSDirectoryMultiIdWidget)
widgetRegistry.register(CPSDirectoryMultiIdWidget)
