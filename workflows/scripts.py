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

from DateTime import DateTime

from Acquisition import aq_parent, aq_inner
from AccessControl import getSecurityManager

from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException

from Products.CPSUtil.mail import send_mail
from Products.CPSUtil.text import get_final_encoding, OLD_CPS_ENCODING
from Products.CPSCore.EventServiceTool import getPublicEventService
from Products.CPSCourrier.relations import make_reply_to
from Products.CPSCourrier.config import (
    BAYES_MIN_PROB,
    STACK_ID,
    REPLY_PTYPE_MAPPING,
)
from Products.CPSCourrier.relations import get_original_message_docid
from Products.CPSCourrier.relations import get_replies_docids

logger = logging.getLogger('CPSCourrier.workflows.scripts')

def bayes_guess_subject(proxy):
    """Update the Subject field with the CPSBayesTool predictions """

    if proxy.portal_type.endswith('Pmail'):
        return

    btool = getToolByName(proxy, 'portal_bayes')
    doc = proxy.getEditableContent()
    data = "%s %s" % (doc['Title'](), doc['content'])
    guessed = btool.guess(data, language=doc['Language']())
    categories = [category for category, probability in guessed
                           if probability >= BAYES_MIN_PROB]
    doc.edit(proxy=proxy, Subject=categories)
    # event is needed for statistics to keep Subjects up to date
    evtool = getPublicEventService(proxy)
    evtool.notifyEvent('cpscourrier_subject_guessed', proxy, {})


def bayes_learn_subject(proxy):
    """Update the bayesian model according to the Subject field value"""
    if proxy.portal_type.endswith('Pmail'):
        return
    btool = getToolByName(proxy, 'portal_bayes')
    doc = proxy.getContent()
    data = "%s %s" % (doc['Title'](), doc['content'])
    for cat in doc['Subject']():
        btool.learn(data, cat, language=doc['Language']())


def reply_to_incoming(incoming_proxy, base_reply_rpath=''):
    """Create an outgoing mail document and update the relation tool

    This function returns the outgoing proxy to be able to redirect to it if
    needed.
    """
    # create the reply
    wftool = getToolByName(incoming_proxy, 'portal_workflow')
    utool = getToolByName(incoming_proxy, 'portal_url')
    portal = utool.getPortalObject()
    incoming_doc = incoming_proxy.getContent()
    incoming_ptype = incoming_doc.portal_type
    container = aq_parent(aq_inner(incoming_proxy))
    container_doc = container.getContent()

    Title = incoming_doc.Title()
    title_lower = Title.lower()
    if not (title_lower.startswith('re:')
            or title_lower.startswith('ref:')):
        Title = 'Re: %s' % Title

    data = {
        'Title': Title,
        'mail_to': [incoming_doc['mail_from']],
        'mail_from': container_doc['from'],
        'Subject': incoming_doc['Subject'](),
    }
    if incoming_doc.portal_type.endswith('Pmail'):
        # bal's email address not relevant. Use two fields for compat
        # later ?
        incoming_to = incoming_doc['mail_to']
        data['mail_from'] = incoming_to and incoming_to[0] or ''
        data['confidential'] = incoming_doc['confidential']

    if base_reply_rpath:
        # initialise it's content with a template or a previously sent reply
        template_proxy = portal.unrestrictedTraverse(base_reply_rpath)
        template_doc = template_proxy.getEditableContent()

        if incoming_ptype == 'Incoming Email':
            # GR I don't see the point of copying the template's Subject.
            # Could even be harmful in case the template just says:
            # "sorry we can't do anything for you" and has for obvious
            # reasons an empty Subject
            data.update({
                'content': template_doc['content'],
                'content_format': template_doc['content_format'],
                'Subject': template_doc['Subject'](),
                'form_of_address': template_doc['form_of_address'],
                })

        # increment the counter of the template reply
        mapping = {'template_usage': template_doc['template_usage'] + 1}
        template_doc._edit(mapping, proxy=template_proxy)

    ptype = REPLY_PTYPE_MAPPING[incoming_ptype]
    oid = container.computeId(Title)
    wftool.invokeFactoryFor(container, ptype, oid, **data)
    outgoing_proxy = getattr(container, oid)

    # update the relation between both docids
    make_reply_to(outgoing_proxy, incoming_proxy)

    # init outgoing's workflow stack
    orig_stack = wftool.getStackFor(incoming_proxy, STACK_ID)
    new_stack = orig_stack.getCopy()
    new_level = new_stack.reverse()
    wftool.doActionFor(outgoing_proxy, 'init_stack',
                       new_stack=new_stack,
                       current_wf_var_id=STACK_ID,
                       current_level=new_level)

    # copy attached files from template
    # now that current user has modif perm
    if base_reply_rpath and template_doc.has_attachment:
        outgoing_doc = outgoing_proxy.getEditableContent()
        fti = template_doc.getTypeInfo()
        tpl_dm = fti.getDataModel(template_doc, proxy=template_proxy)
        data = {}
        wid = 'file'
        n = 0
        while '%s_f0' % wid in tpl_dm:
            new_wid = fti.flexibleAddWidget(outgoing_doc,
                                            'mail_flexible', 'file')
            data['%s_f0' % new_wid] = tpl_dm['%s_f0' % wid]
            n += 1
            wid = 'file_%d' % n

        outgoing_doc.edit(**data)


    # return the outgoing proxy to be able to redirect the user to it
    return outgoing_proxy


def _trigger_transition_for(docid, transition, review_state, context):
    """Trigger the transition for proxies with matching docid and review_state"""
    ptool = getToolByName(context, 'portal_proxies')
    wtool = getToolByName(context, 'portal_workflow')
    for info in ptool.getProxyInfosFromDocid(
        str(docid), workflow_vars=('review_state',)):
        if info['review_state'] != review_state:
            # incoming mail can already have changed state for several
            # reasons, in that case, just ignore it
            logger.debug('ignoring proxy with info %r' % info)
            continue
        logger.debug('trigger %s transition for %r' % (transition, info))
        wtool.doActionFor(info['object'], transition)


def flag_incoming_answered(outgoing_proxy, sci_kw=None):
    """Flag related incoming proxy answered if all replies are sent

    If no incoming mail is found: do nothing (after logging it)
    """
    logger.debug('start flag_incoming_answered')

    ptool = getToolByName(outgoing_proxy, 'portal_proxies')

    # grab the original mail docid
    incoming_docid = get_original_message_docid(outgoing_proxy)
    if incoming_docid is None:
        logger.warning('%r has no related incoming mail: do nothing')
        return

    # final reply: don't check anything and close the incoming

    if sci_kw is not None and sci_kw.get('final_reply'):
        _trigger_transition_for(incoming_docid, 'close', 'answering',
                                outgoing_proxy)
        return

    # check that all replies to the incoming mail are already sent
    outgoing_docids = get_replies_docids(incoming_docid,
                                         context=outgoing_proxy)
    logger.debug('outgoing docids: %r' % (outgoing_docids,))
    for docid in outgoing_docids:
        proxy_infos = ptool.getProxyInfosFromDocid(
            str(docid), workflow_vars=('review_state',))
        for info in proxy_infos:
            # filter out mail templates
            if info['review_state'] in ('pending', 'published'):
                continue
            if info['review_state'] != 'sent':
                # this reply is still not sent: do nothing
                logger.debug('reply with info: %r not sent: do nothing' %
                             info)
                return
    logger.debug('all replies sent')

    # all replies are sent: switch the incoming review state to answered
    _trigger_transition_for(incoming_docid, 'flag_answered', 'answering',
                            outgoing_proxy)

def flag_incoming_answering(outgoing_proxy, sci_kw=None):
    """Flag related incoming proxy answering if in answered state.

    If no incoming mail is found: do nothing (after logging it).
    Used upon reply reactivation
    """
    logger.debug('start flag_incoming_answering')

    ptool = getToolByName(outgoing_proxy, 'portal_proxies')

    # grab the original mail docid
    incoming_docid = get_original_message_docid(outgoing_proxy)
    if incoming_docid is None:
        logger.warning('%r has no related incoming mail: do nothing')
        return

    # all replies are sent: switch the incoming review state to answered
    _trigger_transition_for(incoming_docid, 'flag_answering', 'answered',
                            outgoing_proxy)


def flag_incoming_handled(outgoing_proxy):
    """Flag related incoming proxy handled if outgoing_proxy is the last reply

    outgoing_proxy is to be deleted right after the execution of this script
    """
    logger.debug('start flag_incoming_handled')

    # grab the original mail docid
    incoming_docid = get_original_message_docid(outgoing_proxy)
    if incoming_docid is None:
        logger.warning('%r has no related incoming mail: do nothing')
        return

    # check that outgoing_proxy is the last reply to be deleted
    outgoing_docids = get_replies_docids(incoming_docid,
                                         context=outgoing_proxy)
    if len(outgoing_docids) > 1:
        logger.debug('several remaining docids %r: do nothing' %
                     (outgoing_docids,))
        return

    # this is the last reply, we can trigger the transition for matching proxies
    _trigger_transition_for(incoming_docid, 'flag_handled', 'answering',
                            outgoing_proxy)

def paper_auto_handle(proxy):
    """Trigger handling from default roadmap and go down.

    The idea is that creation are made by the injector."""

    wftool = getToolByName(proxy, 'portal_workflow')
    wftool.doActionFor(proxy, 'handle',
                       use_parent_roadmap=True)
    try:
        wftool.doActionFor(proxy, 'move_down_delegatees',
                           current_wf_var_id=STACK_ID)
    except WorkflowException:
        # This should mean that parent roadmap is empty
        logger.warn(
            "mode_down_delegatees failed for %s (default roadmap empty?)",
            proxy.absolute_url())


def init_stack_with_user(sci, wf_var_id, prefix='courrier_', **kw):
    """Initialize the stack with an element representing current user.

    if 'group' is provided in sci.kwargs, use it instead of the current user

    other kwargs are passed as element metadata.
    use_parent_roadmap is read from the transition kwargs.
    """

    proxy = sci.object
    workflow = sci.workflow
    wftool = getToolByName(proxy, 'portal_workflow')

    group = sci.kwargs.get('group', None)
    if group:
        push_id = '%sgroup:%s' % (prefix, group)
    else:
        # use the current user
        user_id = getSecurityManager().getUser().getId()
        push_id = '%suser:%s' % (prefix, user_id)

    data = dict((key,(value,)) for key, value in kw.items())
    push_args = {'push_ids':(push_id,),
                'data_lists':data.keys()}
    push_args.update(data)
    transition_args = {'current_wf_var_id': wf_var_id}

    # Can't use doActionFor with manage_delegatees or init_stack
    # because the guard cannot be appropriate: we would have to give the
    # handler permanent access to stack management.
    # The stack guard will be checked anyway, so that it isn't a hole
    # to call _executeTransition.

    use_default = sci.kwargs.get('use_parent_roadmap', False)
    if use_default:
        # get copy of the default roadmap
        mailbox = proxy.aq_inner.aq_parent
        stack = wftool.getStackFor(mailbox, STACK_ID)
        new_stack = stack.getCopy()
        # push current user at upper level
        all_levels = stack.getAllLevels()
        if all_levels:
            user_level = all_levels[-1] + 1
        else:
            user_level = 0
        new_stack.push(levels=(user_level,), **push_args)
        # init with our copy
        tdef = workflow.transitions.get('init_stack')
        transition_args.update({'new_stack': new_stack,
                                'current_level': user_level})
        workflow._executeTransition(proxy, tdef, transition_args)
    else:
        # simply use manage_delegatees transition with kwargs for push
        push_args['levels'] = (0,)
        transition_args.update(push_args)
        tdef = workflow.transitions.get('manage_delegatees')
        workflow._executeTransition(proxy, tdef, transition_args)

#
# Mail sending operation
#

def _quote_mail(proxy, encoding=OLD_CPS_ENCODING, plain_text=True):
    """Helper function to quote a mail in a reply or a forward"""
    tstool = getToolByName(proxy, 'translation_service')
    doc = proxy.getContent()
    orig_date_str = doc['CreationDate']()
    year, month, day = orig_date_str.split()[0].split('-')
    quote_header = tstool('On ${y}-${m}-${d}, ${name} wrote:',
                          {'y': year,
                           'm': month,
                           'd': day,
                           'name': doc['mail_from'],
                          }).encode(encoding)
    body = '\n\n%s\n' % quote_header
    lines =  doc['content'].split('\n')
    body += '\n'.join('> %s' % line for line in lines)
    if not plain_text:
        return '\n<pre>%s</pre>\n' % body
    return body

def _extract_attachments(proxy, filters=None):
    """Extract File/Image fields related data from a proxy

    Return a generator of tuples (title, ctype, data)
    """
    if filters is None:
        # default fields type that potentially host attachments
        filters = set(['CPS File Field',
                       'CPS Disk File Field',
                       'CPS Image Field'])
    doc = proxy.getContent()
    dm = doc.getDataModel()
    schemas = proxy.getTypeInfo()._listSchemas(doc)

    # collecting interesting fields
    fields = [(f_id, f) for schema in schemas
                        for f_id, f in schema.items()
                        if f.meta_type in filters and dm[f_id] is not None]
    fields_dict = dict(fields)

    # removing fields that are helpers for pure data fields
    to_remove = set()
    suffix_classes = ('suffix_text', 'suffix_html', 'suffix_html_subfiles')
    for f_id, f in fields:
        for suffix_class in suffix_classes:
            suffix = getattr(f, suffix_class, None)
            if suffix:
                helper_f_id = f_id + suffix
                if helper_f_id in fields_dict:
                    to_remove.add(helper_f_id)

    # extracting interesting data out of the datamodel
    attachments = []
    for f_id, _ in fields:
        if f_id not in to_remove:
            v= dm[f_id]
            attachments.append((v.title, v.getContentType(), str(v)))
    return attachments

def forward_mail(proxy, mto, comment=''):
    """Forward an incoming mail to another external mailbox"""
    tstool = getToolByName(proxy, 'translation_service')
    encoding = get_final_encoding(tstool)

    mailbox_doc = aq_parent(aq_inner(proxy)).getContent()
    mfrom = mailbox_doc['from']
    subject = "Fwd: " + proxy.Title()

    body = comment
    body += _quote_mail(proxy)

    attachments = _extract_attachments(proxy)

    return send_mail(proxy, mto, mfrom, subject, body, attachments=attachments,
                     encoding=encoding)

HTML_BODY_WRAPPER = """\
<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
<html>
<head>
  <meta content="text/html;charset=%s" http-equiv="Content-Type">
  <title></title>
</head>
<body bgcolor="#ffffff" text="#000000">%s</body>
</html>"""

# make emacs fontifier happy
dummy = """ " """

def compute_reply_body(proxy, plain_text=True, additionnal_info=''):
    """Compute the body of a sent outgoing mail

    The content of the reply is build from the proxy quoting the original mail
    thanks to the relation graph.
    """
    if proxy.portal_type.endswith('Pmail'):
        return ''

    tstool = getToolByName(proxy, 'translation_service')
    encoding = get_final_encoding(tstool)
    vtool = getToolByName(proxy, 'portal_vocabularies')
    mcat = lambda label: tstool(label).encode(encoding)
    doc = proxy.getContent()
    body = doc['content']

    foa = vtool.form_of_address.getMsgid(doc['form_of_address'])
    if foa:
        foa = mcat(foa)
    else:
        foa = vtool.form_of_address[doc['form_of_address']]

    if plain_text:
        sig_wrapper = '\n\n%s\n\n-- \n%s\n%s'
    else:
        sig_wrapper =  '<br/><br/>%s<br/><br/>-- <br/>%s<br/>%s'
    body += sig_wrapper % (foa , doc['signature'], additionnal_info)

    # get the original content for quoting
    incoming_docid = get_original_message_docid(proxy)
    if incoming_docid is None:
        logger.warning('%r has no related incoming mail: do not include'
                       'original mail in reply' % proxy)
    else:
        ptool = getToolByName(proxy, 'portal_proxies')
        for info in ptool.getProxyInfosFromDocid(str(incoming_docid)):
            if info['visible']:
                body += _quote_mail(info['object'], encoding,
                                    plain_text=plain_text)

    if plain_text:
        return body
    else:
        return HTML_BODY_WRAPPER % (encoding.upper(), body)


def send_reply(proxy, text_only=False, additionnal_info='', sci_kw=None):
    """Send a reply by SMTP

    If text_only is True, any html is stripped to plain text
    Otherwise, the content type is deduced from the document.
    """
    if proxy.portal_type == 'Outgoing Pmail':
        return
    tstool = getToolByName(proxy, 'translation_service')
    encoding = get_final_encoding(tstool)
    doc = proxy.getContent()
    mto = doc['mail_to']
    mcc = doc['mail_cc']
    mfrom = doc['mail_from']
    subject = doc['Title']()

    plain_text = text_only or getattr(doc, 'content_format', 'text') != 'html'

    body = compute_reply_body(proxy, additionnal_info=additionnal_info,
                              plain_text=plain_text)
    attachments = _extract_attachments(proxy)

    doc = proxy.getEditableContent()
    # bypass the ModifyPortalContent permission check for validated mails
    doc._edit(EffectiveDate=DateTime())

    # send mail at last to avoid side effect in case of uncatched exception
    res = send_mail(doc, mto, mfrom, subject, body, mcc=mcc,
                   attachments=attachments, encoding=encoding,
                   plain_text=plain_text)

    return res

