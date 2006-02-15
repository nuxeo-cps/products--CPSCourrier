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

""" Adapters for CPS Courrier import/export."""
from zope.app import zapi
from zope.component import adapts
from zope.interface import implements

from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.utils import exportObjects
from Products.GenericSetup.utils import importObjects
from Products.GenericSetup.utils import XMLAdapterBase
from Products.GenericSetup.utils import ObjectManagerHelpers
from Products.GenericSetup.utils import PropertyManagerHelpers

from Products.GenericSetup.interfaces import INode
from Products.GenericSetup.interfaces import IBody
from Products.GenericSetup.interfaces import ISetupEnviron

from Products.CPSCourrier.interfaces import (
    IColumnDefinitionsTool, IColumnDefinition
    )

TOOL = 'portal_columns'
NAME = 'columns' 

def exportColumnDefinitionsTool(context):
    """Export columns definitions tool and the definitions it holds as a set of XML files.
    """
    site = context.getSite()
    tool = getToolByName(site, TOOL, None)
    if tool is None:
        logger = context.getLogger(NAME)
        logger.info("Nothing to export.")
        return
    exportObjects(tool, '', context)

def importColumnDefinitionsTool(context):
    """Import columns definitions tool and the definitions it holds as a set of XML files.    """
    site = context.getSite()
    tool = getToolByName(site, TOOL)
    importObjects(tool, '', context)


class ColumnDefinitionsToolXMLAdapter(XMLAdapterBase, ObjectManagerHelpers,
                           PropertyManagerHelpers):
    """ XML importer and exporter for Upload Taker tool.
    """

    name = NAME
    
    adapts(IColumnDefinitionsTool, ISetupEnviron)
    implements(IBody)

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        node.appendChild(self._extractProperties())
        node.appendChild(self._extractObjects())
        self._logger.info("Columns definition tool exported.")
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        if self.environ.shouldPurge():
            self._purgeProperties()
            self._purgeObjects()
        self._initProperties(node)
        self._initObjects(node)
        self._logger.info("Columns definition tool imported.")

    node = property(_exportNode, _importNode)


class ColumnDefinitionXMLAdapter(XMLAdapterBase, PropertyManagerHelpers):
    """ XML importer and exporter for Upload Taker tool.
    """

    adapts(IColumnDefinition, ISetupEnviron)
    implements(IBody)

    def _exportNode(self):
        """Export the object as a DOM node.
        """
        node = self._getObjectNode('object')
        node.appendChild(self._extractProperties())
        self._logger.info("Column definition exported.")
        return node

    def _importNode(self, node):
        """Import the object from the DOM node.
        """
        if self.environ.shouldPurge():
            self._purgeProperties()
        self._initProperties(node)
        self._logger.info("Column definition imported.")

    node = property(_exportNode, _importNode)
