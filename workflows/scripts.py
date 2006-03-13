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
import logging
from Acquisition import aq_parent, aq_inner

from Products.CMFCore.utils import getToolByName
from Products.CPSCourrier.config import RELATION_GRAPH_ID

logger = logging.getLogger('CPSCourrier')

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
    rtool = getToolByName(incoming_proxy, 'portal_relations')
    rtool.addRelationFor(RELATION_GRAPH_ID,
                         int(outgoing_proxy.getDocid()),
                         'is_reply_to',
                         int(incoming_proxy.getDocid()))
    return outgoing_proxy


def flag_incoming_answered(outgoing_proxy):
    """Flag related incoming proxy answered if all replies are sent

    If no incoming mail is found: do nothing (after logging it)
    """
    rtool = getToolByName(outgoing_proxy, 'portal_relations')
    ptool = getToolByName(outgoing_proxy, 'portal_proxies')
    wtool = getToolByName(outgoing_proxy, 'portal_workflow')
    # get the related incoming mail
    incoming_docids = rtool.getRelationsFor(RELATION_GRAPH_ID,
                                            int(outgoing_proxy.getDocid()),
                                            'is_reply_to')
    if not incoming_docids:
        # the related incoming mail has been deleted
        logger.warning('%r has no related incoming mail: do nothing')
        return
    # a is_reply_to is a "many to one" relation
    (incoming_docid,) = incoming_docids

    # check that all replies to the incoming mail are already sent
    outgoing_docids = rtool.getRelationsFor(RELATION_GRAPH_ID,
                                            int(incoming_docid),
                                            'has_reply')
    for docid in outgoing_docids:
        proxy_infos = ptool.getProxyInfosFromDocid(
            str(docid), workflow_vars=('review_state',))
        for info in proxy_infos:
            if info['review_state'] is not 'sent':
                # this reply is still not sent: do nothing
                return

    # all replies are sent: switch the incoming review state to answered
    for info in ptool.getProxyInfosFromDocid(
        str(incoming_docid), workflow_vars=('review_state',)):
        if info['review_state'] is not 'answering':
            # incoming mail can already have changed state for several reasons,
            # in that case, just ignore it
            continue
        wtool.doActionFor(info['object'], 'flag_answered')




