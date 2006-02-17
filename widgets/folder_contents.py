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


""" Folder Contents Portlet Widgets. """

from zLOG import LOG, DEBUG
from Globals import InitializeClass
from AccessControl import Unauthorized

from Products.CMFCore.utils import _checkPermission
from Products.CMFCore.permissions import ListFolderContents

from Products.CPSSchemas.Widget import CPSWidget
from Products.CPSSchemas.Widget import widgetRegistry
from Products.CPSSchemas.DataModel import DataModel
from Products.CPSSchemas.DataStructure import DataStructure

from Products.CPSCourrier.widgets.tabular import TabularWidget

class FolderContentsWidget(TabularWidget):
    """ A tabular portlet widget that performs a simple folder listing.

    Information is fetched from the folder's objects of a given meta-type.
    There's no batching or sorting. 

    >>> FolderContentsWidget('the_id')
    <FolderContentsWidget at the_id>
    """

    meta_type = "Folder Contents Widget"
    _properties = TabularWidget._properties + (
        {'id': 'listed_meta_types', 'type': 'list', 'mode': 'w',
         'label': 'Meta types to list', 'is_required' : 1},
        )

    listed_meta_types = (
       'CPS Proxy Document',
       'CPS Proxy Folder',
       'CPS Proxy Folderish Document',
       )

    def listRowDataModels(self, datastructure, **kw):
        """Return an iterator for folder contents datamodels
        """
        folder = kw.get('context_obj') # typical of portlets
        if folder is None:
            folder = datastructure.getDataModel().getProxy()
        
        if not _checkPermission(ListFolderContents, folder):
            raise Unauthorized("You are not allowed to list this folder")
        meta_types = datastructure.get('meta_types') or self.listed_meta_types

        iterprox = (folder[p_id] for p_id in folder.objectIds(meta_types))
        iterdocs = ( (proxy.getContent(), proxy) for proxy in iterprox)
        return (doc.getTypeInfo().getDataModel(doc, proxy=proxy, context=folder)
                for doc, proxy in iterdocs)

widgetRegistry.register(FolderContentsWidget)
