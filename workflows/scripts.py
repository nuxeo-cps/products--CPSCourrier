# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
# Author: Olivier Grisel <ogrisel@nuxeo.com>
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
"""Non restricted code to perform various workflow related tasks.

These functions are usually called by workflow scripts.
"""
from Acquisition import aq_parent, aq_inner

from Products.CMFCore.utils import getToolByName
from Products.CPSCourrier.config import RELATION_GRAPH_ID

def reply_to_incoming(incoming_proxy):
    """Create an outgoing mail document and update the relation tool

    This function returns the outgoing proxy to be able to redirect to it if
    needed.
    """
    # create the reply
    wftool = getToolByName(incoming_proxy, 'portal_workflow')
    incoming_doc = incoming_proxy.getContent()
    container = aq_parent(aq_inner(incoming_proxy))
    container_doc = container.getContent()

    Title = incoming_doc.Title()
    title_lower = Title.lower()
    if not (title_lower.startswith('re:') or
            title_lower.startswith('ref:')):
        Title = 'Re: %s' % Title

    data = {
        'Title': Title,
        'to': [incoming_doc['from']],
        'from': container_doc['from'],
    }

    ptype = 'Outgoing Mail'
    fti = getToolByName(incoming_proxy, 'portal_types')[ptype]
    dm = fti.getDataModel(None)
    oid = container.computeId(Title)
    wftool.invokeFactoryFor(container, ptype, oid, datamodel=dm, **data)
    outgoing_proxy = getattr(container, oid)

    # update the relation between both docids
    #rtool = getToolByName(incoming_proxy, 'portal_relations')
    #graph = rtool[RELATION_GRAPH_ID]

    return outgoing_proxy





