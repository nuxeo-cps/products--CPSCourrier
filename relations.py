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
"""Non restricted code to perform queries on the relations graph"""
import logging

from Products.CMFCore.utils import getToolByName
from Products.CPSSchemas.DataStructure import DataStructure
from Products.CPSCourrier.config import (
    RELATION_GRAPH_ID, RELATION_PREFIX, HAS_REPLY)
from Products.CPSRelation.interfaces import IVersionHistoryResource
from Products.CPSRelation.statement import Statement
from Products.CPSRelation.node import PrefixedResource, VersionHistoryResource

logger = logging.getLogger('CPSCourrier.relations')

#
# Common helpers
#

def _get_graph(context):
    rtool = getToolByName(context, 'portal_relations')
    return rtool.getGraph(RELATION_GRAPH_ID)

#
# Adding new statements to the graph
#

def make_reply_to(reply_proxy, reference_proxy):
    """Add relation so that proxy is a reply to reference_proxy"""
    graph = _get_graph(reply_proxy)
    statement = Statement(
        IVersionHistoryResource(reference_proxy),
        PrefixedResource(RELATION_PREFIX, HAS_REPLY),
        IVersionHistoryResource(reply_proxy),
    )
    graph.add([statement])

#
# Removing statements from the graph
#

def clean_relations_for(proxy):
    """Remove all statements that involve proxy"""
    graph = _get_graph(proxy)
    has_reply_resource = PrefixedResource(RELATION_PREFIX, HAS_REPLY)
    patterns = (
        Statement(IVersionHistoryResource(proxy), has_reply_resource, None),
        Statement(None, has_reply_resource, IVersionHistoryResource(proxy)),
    )
    statements_to_remove = []
    for pattern in patterns:
        statements_to_remove.extend(graph.getStatements(pattern))
    graph.remove(statements_to_remove)

def unlink(original, reply):
    """Break the reply relation between two proxies"""
    graph = _get_graph(original)
    statement = Statement(
        IVersionHistoryResource(original),
        PrefixedResource(RELATION_PREFIX, HAS_REPLY),
        IVersionHistoryResource(reply),
    )
    graph.remove([statement])

#
# Find directly related mails
#

def _resource_from_docid_or_proxy(docid_or_proxy):
    if isinstance(docid_or_proxy, basestring):
        return VersionHistoryResource(docid_or_proxy)
    return IVersionHistoryResource(docid_or_proxy)

def get_original_message_docid(reply, context=None):
    """Helper function that returns the docid of the related orgininal mail

    `reply` can be a docid or a proxy.

    Return None is no related original mail.
    """
    if context is not None:
        graph = _get_graph(context)
    else:
        graph = _get_graph(reply)
    reply_node = _resource_from_docid_or_proxy(reply)
    original_msg_nodes = graph.getSubjects(
        PrefixedResource(RELATION_PREFIX, HAS_REPLY), reply_node)
    original_msg_docids = [node.docid for node in original_msg_nodes]

    logger.debug('original message docids: %r' % (original_msg_docids,))
    if not original_msg_docids:
        # the related incoming mail has been deleted
        return None
    # a is_reply_to is a "many to one" relation
    (original_msg_docid,) = original_msg_docids
    logger.debug('original msg docid: %r', original_msg_docid)
    return original_msg_docid

def get_replies_docids(original_msg, context=None):
    """List replies docids for a given mail proxy"""
    if context is not None:
        graph = _get_graph(context)
    else:
        graph = _get_graph(original_msg)
    original_msg_node = _resource_from_docid_or_proxy(original_msg)
    replies_nodes = graph.getObjects(original_msg_node,
                                     PrefixedResource(RELATION_PREFIX, HAS_REPLY))
    return [node.docid for node in replies_nodes]

#
# Thread extraction (find inderictly connected mails)
#

def _find_root(graph, start_from):
    """Recursively climb the replies tree in graph till the root"""
    parents = graph.getSubjects(PrefixedResource(RELATION_PREFIX, HAS_REPLY),
                                start_from)
    if not parents:
        # start_from is the root
        return start_from
    else:
        # HAS_REPLY is supposed to be an (one to *) relation
        (parent,) = parents
        return _find_root(graph, parent)


def _accumulate_proxy_info(graph, start_from, ptool, depth=0, from_widget=None):
    """Recursively accumulate proxy info by walking down the HAS_REPLY tree

    Return an ordered list of tuples (depth, proxy_info)
    """
    # compute current level

    wanted_vars = ('review_state',)
    infos = ptool.getProxyInfosFromDocid(start_from.docid, workflow_vars=wanted_vars)

    # filter out proxies that are used as templates
    template_states = ('pending', 'published')

    infos = [(depth, info) for info in infos
                           if info['review_state'] not in template_states
                              and info['visible']]

    for info in infos:
        proxy = info[1]['object']
        doc = proxy.getContent()
        if from_widget is not None and doc.portal_type.endswith('Pmail'):
            dm = doc.getDataModel(proxy=proxy)
            ds = DataStructure(datamodel=dm)
            from_widget.prepare(ds)
            info[1]['from'] = from_widget.render('view', ds)
        else:
            info[1]['from'] = doc.mail_from

    # adding depth first children info
    depth += 1
    children = graph.getObjects(start_from,
                                PrefixedResource(RELATION_PREFIX, HAS_REPLY))
    for child in children:
        child_info = _accumulate_proxy_info(graph, child, ptool, depth)
        infos.extend(child_info)
    return infos


def get_thread_for(proxy):
    """Get related proxies info according to the rtool

    Algorithm: climb the HAS_REPLY tree to the root and then walk it down depth-first

    Return an ordered list of tuples (depth, proxy_info)
    """
    logger.debug('get_thread_for %r', proxy)
    ptool = getToolByName(proxy, 'portal_proxies')
    g = _get_graph(proxy)

    # climb till the root
    root_node = _find_root(g, IVersionHistoryResource(proxy))
    logger.debug('root found: %s' % root_node.docid)

    # try and find a rendering widget for the mail_from field
    from_widget = None
    ltool = getToolByName(proxy, 'portal_layouts')
    if proxy.portal_type.endswith('Pmail'):
        from_widget = ltool['pmail_common']['from']

    # walk back down collecting proxy infos
    infos = _accumulate_proxy_info(g, root_node, ptool, from_widget=from_widget)
    logger.debug('collected thread infos: %r' % infos)

    return infos


