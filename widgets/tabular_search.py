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

from Products.CPSCourrier.widgets.tabular import TabularWidget
from Products.CPSCourrier.braindatamodel import BrainDataModel

QUERY_PROP_PREFIX = 'query_'
QUERY_PROP_PREFIX_len = len(QUERY_PROP_PREFIX)

_missed = object()

class TabularSearchWidget(TabularWidget):
    """ A tabular widget that performs a catalog query.

    query parameters are obtained from (by descending order of precedence)
    - cookie or other transient stuff
    - datastructure
    - properties
    """

    _query_properties = (
        {'id': 'query_folder_prefix', 'type' : 'string', 'mode' : 'w'},
        {'id': 'query_portal_type', 'type' : 'string', 'mode' : 'w'},
        {'id': 'query_review_state', 'type' : 'string', 'mode' : 'w'},
        )

    _properties = TabularWidget._properties + _query_properties + (
        # this one tells which ds keys to use to build the query
            {'id': 'query_widgets', 'type' : 'tokens', 'mode' : 'w'},)


    def _buildQuery(self, datastructure, **kw):

        # initiate from non void properties of self
        query_props = ((prop['id'], getattr(self, prop['id'])
                        for prop in self._query_properties))
        query = dict( (key[QUERY_PROP_PREFIX_LEN:], item)
                      for key, item in query_props if item)

        # update from datastructure
        query_from_ds = ( (key, datastructure.get(key, _missed))
                     for key in query_params_list)
        query.update(dict(
            (key, item) for key_item in query_from_ds
            if item is not _missed
            ))

        # transient stuff not implemented
        return query

    def listRowDatamodels(self, datastructure, **kw):
        """ do the query. """

        query = self._buildQuery(datastructure, **kw)
        
        context = kw['context-obj'] # same remark as for folder_contents, should
        # be factorized in base-class
        brains = context.search(query)

        return (BrainDataModel(brain) for brain in brains)
    
