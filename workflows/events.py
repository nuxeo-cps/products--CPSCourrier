# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
# Author: Olivier Grisel <ogrisel@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# bythe Free Software Foundation.
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
"""Event handlers for workflow event and relation graph updates

This handlers are registered using the Zope3-style events and registered through
zcml at Zope init time.
"""
import logging

from Products.CMFCore.utils import getToolByName
from Products.CPSCourrier.config import RELATION_GRAPH_ID

logger = logging.getLogger('CPSCourrier.workflows.events')

def removedProxy(ob, event):
    """A document was deleted, we need clean the relations graph

    All relations involving the docid of the given object are deleted if it was
    the last proxy for that docid.
    """
    ptool = getToolByName(ob, 'portal_proxies')
    docid = ob.getDocid()

    # check if there remain living proxies refering to that docid
    proxies = ptool.listProxies(docid=docid)
    if len(proxies):
        logger.debug('remaining several proxies %r: do nothing' %
                     (proxies,))
        return

    # this was the last proxy for that docid, clean the remaining relations
    logger.debug('cleaning all relations for proxy %r with docid %s' %
                 (ob, docid))
    rtool = getToolByName(ob, 'portal_relations', None)
    if rtool is not None:
        rtool.removeAllRelationsFor(RELATION_GRAPH_ID, int(docid))


