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
import smtplib
import socket
from Acquisition import aq_parent, aq_inner
from AccessControl import getSecurityManager

from Products.CMFCore.utils import getToolByName
from Products.CPSCourrier.config import (
    RELATION_GRAPH_ID,
    IS_REPLY_TO,
    HAS_REPLY,
)

logger = logging.getLogger('CPSCourrier.workflows.scripts')

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
                         IS_REPLY_TO,
                         int(incoming_proxy.getDocid()))
    return outgoing_proxy


def _get_incoming_docid_for(outgoing_proxy):
    """Helper function that returns the docid of the related incoming mail

    Return None is no related docid is found
    """
    rtool = getToolByName(outgoing_proxy, 'portal_relations')
    # get the related incoming mail
    incoming_docids = rtool.getRelationsFor(RELATION_GRAPH_ID,
                                            int(outgoing_proxy.getDocid()),
                                            IS_REPLY_TO)
    logger.debug('incoming docids: %r' % (incoming_docids,))
    if not incoming_docids:
        # the related incoming mail has been deleted
        return None
    # a is_reply_to is a "many to one" relation
    (incoming_docid,) = incoming_docids
    logger.debug('incoming docid: %r' % (incoming_docid,))
    return incoming_docid


def _trigger_transition_for(docid, transition, review_state, context):
    """Trigger the transition for proxies with matching docid and review_state"""
    ptool = getToolByName(context, 'portal_proxies')
    wtool = getToolByName(context, 'portal_workflow')
    for info in ptool.getProxyInfosFromDocid(
        str(docid), workflow_vars=('review_state',)):
        if info['review_state'] != review_state:
            # incoming mail can already have changed state for several reasons,
            # in that case, just ignore it
            logger.debug('ignoring proxy with info %r' % info)
            continue
        logger.debug('trigger %s transition for %r' % (transition, info))
        wtool.doActionFor(info['object'], transition)


def flag_incoming_answered(outgoing_proxy):
    """Flag related incoming proxy answered if all replies are sent

    If no incoming mail is found: do nothing (after logging it)
    """
    logger.debug('start flag_incoming_answered')

    rtool = getToolByName(outgoing_proxy, 'portal_relations')
    ptool = getToolByName(outgoing_proxy, 'portal_proxies')

    # grab the original mail docid
    incoming_docid = _get_incoming_docid_for(outgoing_proxy)
    if incoming_docid is None:
        logger.warning('%r has no related incoming mail: do nothing')
        return

    # check that all replies to the incoming mail are already sent
    outgoing_docids = rtool.getRelationsFor(RELATION_GRAPH_ID,
                                            int(incoming_docid),
                                            HAS_REPLY)
    logger.debug('outgoing docids: %r' % (outgoing_docids,))
    for docid in outgoing_docids:
        proxy_infos = ptool.getProxyInfosFromDocid(
            str(docid), workflow_vars=('review_state',))
        for info in proxy_infos:
            if info['review_state'] != 'sent':
                # this reply is still not sent: do nothing
                logger.debug('reply with info: %r not sent: do nothing' %
                             info)
                return
    logger.debug('all replies sent')

    # all replies are sent: switch the incoming review state to answered
    _trigger_transition_for(incoming_docid, 'flag_answered', 'answering',
                            outgoing_proxy)


def flag_incoming_handled(outgoing_proxy):
    """Flag related incoming proxy handled if outgoing_proxy is the last reply

    outgoing_proxy is to be deleted right after the execution of this script
    """
    logger.debug('start flag_incoming_handled')

    rtool = getToolByName(outgoing_proxy, 'portal_relations')

    # grab the original mail docid
    incoming_docid = _get_incoming_docid_for(outgoing_proxy)
    if incoming_docid is None:
        logger.warning('%r has no related incoming mail: do nothing')
        return

    # check that outgoing_proxy is the last reply to be deleted
    outgoing_docids = rtool.getRelationsFor(RELATION_GRAPH_ID,
                                            int(incoming_docid),
                                            HAS_REPLY)
    if len(outgoing_docids) > 1:
        logger.debug('several remaining docids %r: do nothing' %
                     (outgoing_docids,))
        return

    # this is the last reply, we can trigger the transition for matching proxies
    _trigger_transition_for(incoming_docid, 'flag_handled', 'answering',
                            outgoing_proxy)


def init_stack_with_user(sci, wf_var_id, prefix='user_wdata', **kw):
    """Initialize the stack with an element representing current user.

    other kwargs are passed as element metadata."""

    proxy = sci.object
    workflow = sci.workflow
    wftool = getToolByName(proxy, 'portal_workflow')

    data = dict((key,(value,)) for key, value in kw.items())
    user_id = getSecurityManager().getUser().getId()

    # Can't use doActionFor because the security checks are inappropriate
    # (cannot give the user's role a permanent access to the stack)
    # canManageStack will be checked under the hood, with the special condition
    # for empty stakcs.
    tdef = workflow.transitions.get('manage_delegatees')
    kwargs = {'current_wf_var_id': wf_var_id,
              'levels': (0,),
              'push_ids':('%s:%s' % (prefix, user_id),),
              'data_lists':data.keys()}
    kwargs.update(data)


    workflow._executeTransition(proxy, tdef, kwargs)


def compute_reply_body(reply_proxy, encoding='iso-8859-15'):
    """Compute the body of a sent outgoing mail

    The content of the reply is build from the proxy quoting the original mail
    thanks to the relation graph.
    """
    mcat = getToolByName(reply_proxy, 'translation_service')
    reply_doc = reply_proxy.getContent()
    body = reply_doc['content']

    # get the original content for quoting
    incoming_docid = _get_incoming_docid_for(reply_proxy)
    if incoming_docid is None:
        logger.warning('%r has no related incoming mail: do not include'
                       'original mail in reply' % reply_proxy)
    else:
        ptool = getToolByName(reply_proxy, 'portal_proxies')
        for info in ptool.getProxyInfosFromDocid(str(incoming_docid)):
            if info['visible']:
                incoming_doc = info['object'].getContent()
                orig_date_str = incoming_doc['CreationDate']()
                year, month, day = orig_date_str.split()[0].split('-')
                quote_header = mcat('On ${y}-${m}-${d}, ${name} wrote:',
                                    {'y': year,
                                     'm': month,
                                     'd': day,
                                     'name': incoming_doc['from']}
                                   ).encode(encoding)
                body += '\n\n%s\n' % quote_header
                lines =  incoming_doc['content'].split('\n')
                body += '\n'.join('> %s' % line for line in lines)
    return body


def send_reply(reply_proxy, encoding='iso-8859-15'):
    """Send a reply


    This function does not do any error handling if the Mailhost fails to send
    it properly. This will be handled by the skins script along with the
    redirect if needed.
    """
    reply_doc = reply_proxy.getContent()
    body = compute_reply_body(reply_proxy, encoding)

    # send the mail
    mailhost = getToolByName(reply_proxy, 'MailHost')
    kw = {'mto': reply_doc['to'],
          'mfrom': reply_doc['from'],
          'subject': reply_doc['Title']()}
    try:
        return mailhost.send(body, **kw)
    # if anything went wrong: log the error for the admin and raise an exception
    # of type IOError or ValueError that will be cactched by the skins script in
    # order to build a friendly user message
    except (socket.error, smtplib.SMTPServerDisconnected), e:
        logger.error("error sending email (%s, %r): %s" % (body, kw, e))
        raise IOError(e)
    except smtplib.SMTPRecipientsRefused, e:
        logger.error("error sending email (%s, %r): %s" % (body, kw, e))
        raise ValueError('invalid_recipients_address')
    except smtplib.SMTPSenderRefused, e:
        logger.error("error sending email (%s, %r): %s" % (body, kw, e))
        raise ValueError('invalid_sender_address')


