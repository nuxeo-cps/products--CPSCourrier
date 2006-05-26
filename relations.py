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
"""Non restricted code to perform queries on the relations graph
"""
import logging
from Acquisition import aq_parent, aq_inner

from Products.CMFCore.utils import getToolByName
from Products.CPSCourrier.config import (
    RELATION_GRAPH_ID, IS_REPLY_TO, HAS_REPLY)

logger = logging.getLogger('CPSCourrier.relations')

def make_reply_to(proxy, reference_proxy):
    """Add relation so that proxy is a reply to reference_proxy"""
    rtool = getToolByName(proxy, 'portal_relations')
    rtool.addRelationFor(RELATION_GRAPH_ID,
                         int(proxy.getDocid()),
                         IS_REPLY_TO,
                         int(reference_proxy.getDocid()))

def _find_root(graph, start_from, relation_id=IS_REPLY_TO):
    """Recursively climb the relation_id tree in graph till the root"""
    parents = graph.getRelationsFor(start_from, relation_id)
    if not parents:
        # start_from is the root
        return start_from
    else:
        # relation_id is supposed to be an (* to one) relation
        (parent,) = parents
        return _find_root(graph, parent, relation_id)


def _accumulate_proxy_info(graph, start_from, ptool,
                           depth=0, relation_id=HAS_REPLY):
    """Recursively accumulate proxy info by walking down the relation_id tree
    depth-first

    Return an ordered list of tuples (depth, proxy_info)
    """
    # compute current level
    infos = ptool.getProxyInfosFromDocid(str(start_from),
                                         workflow_vars=('review_state',))
    infos = [(depth, info) for info in infos if info['visible']]

    # adding depth first children info
    depth += 1
    children = graph.getRelationsFor(start_from, relation_id)
    for child in children:
        child_info = _accumulate_proxy_info(graph, child, ptool, depth,
                                            relation_id)
        infos.extend(child_info)
    return infos


def get_thread_for(proxy):
    """Get related proxies info according to the rtool

    Algorithm: climb the 'IS_REPLY_TO' tree to the root and then walk it down
    depth-first

    Return an ordered list of tuples (depth, proxy_info)
    """
    logger.debug('get_thread_for %r' % proxy)
    rtool = getToolByName(proxy, 'portal_relations')
    ptool = getToolByName(proxy, 'portal_proxies')
    g = rtool.getGraph(RELATION_GRAPH_ID)

    # climb till the root
    root_id = _find_root(g, int(proxy.getDocid()), IS_REPLY_TO)
    logger.debug('root found: %d' % root_id)

    # walk back down collecting proxy infos
    infos = _accumulate_proxy_info(g, root_id, ptool, relation_id=HAS_REPLY)
    logger.debug('collected thread infos: %r' % infos)

    return infos



