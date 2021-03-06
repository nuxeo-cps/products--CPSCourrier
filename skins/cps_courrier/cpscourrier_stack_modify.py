##parameters=workflow_action_form, current_var_id, REQUEST=None, **kw
# -*- coding: iso-8859-15 -*-
# Copyright (c) 2004-2005 Minist�re de la justice <http://www.justice.gouv.fr/>
# Copyright (c) 2004-2005 Capgemini <http://capgemini.com>
# Copyright (c) 2004-2005 Nuxeo SARL <http://nuxeo.com>
# Authors: Anahide Tchertchian <at@nuxeo.com>
#          Georges Racinet <gracinet@nuxeo.com>
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
#-------------------------------------------------------------------------------
# $Id$
"""Change delegation stack (by adding or removing people from the stack)

That's because additions and deletions are handled by the same wf transition in
our case. It is also possible to perform editions.

Needed parameters:
- workflow_action_form (template used)
- current_var_id (stack variable id)

Optional kws:

The type of action is specified by the presence of one of these keys in the
form:
- submit_add, submit_delete, submit_edit


Needed by wf stacks:

Add elements:
- push_ids: ids to be pushed in stack
- level: level chosen
- data_lists: list of stack elements data keys
- other elements must include those specified in data_lists and be lists
  See the push examples in CPSCourrier/doc/developer/stacks.txt (parameter
  naming is identical)

Delete elements:
- pop_ids: ids to be removed from the stack (convention:
  'level,prefixed_elt_id')

Edit elements: same as add elements except:
- edit_ids: ids to be edited (the entire list but well)
  otherwise see Add elements
"""

from logging import getLogger

from urllib import urlencode
from re import match
from DateTime import DateTime

from Products.CMFCore.utils import getToolByName

logger = getLogger('CPSCourrier.skins.cpscourrier.cpscourrier_stack_modify')

workflow_actions = {'pop': 'manage_delegatees',
                    'push': 'manage_delegatees',
                    'edit': 'manage_delegatees',
                    'move_down' : 'move_down_delegatees',
                    }

if REQUEST is not None:
    kw.update(REQUEST.form)

if 'submit_delete' in kw:
    action_type = 'pop'
elif 'submit_add' in kw:
    action_type ='push'
elif 'submit_edit' in kw:
    action_type = 'edit'
elif 'submit_move_down' in kw:
    action_type = 'move_down'
    if REQUEST is not None:
	url = '%s/workflow_transition_form?transition=%s' % (
	    context.absolute_url(), 
	    workflow_actions[action_type])
	REQUEST.RESPONSE.redirect(url)
	return
else:
    raise ValueError("Unkown submission type")

workflow_action = workflow_actions.get(action_type)
#
# helper method
#
def makeDate(date):
    """Make a DateTime object from given string date

    date format is dd/mm/yyyy

    Raise ValueError if date is invalid
    """
    if not date:
        v = None
    else:
        if match(r'^[0-9]?[0-9]/[0-9]?[0-9]/[0-9]{2,4}$', date) is not None:
            d, m, y = date.split('/')
        else:
            raise ValueError(date)
        try:
            v = DateTime(int(y), int(m), int(d))
        except (ValueError, TypeError, DateTime.DateTimeError,
                DateTime.SyntaxError, DateTime.DateError):
            raise ValueError(date)
    return v


res = None
psm = ''
err = 0

wftool = getToolByName(context, 'portal_workflow')

# used for redirection
old_state = wftool.getInfoFor(context, 'review_state', None)

logger.debug("kws = %s", kw)

kw['current_wf_var_id'] = current_var_id

# XXX GR TODO. now that everything is a transition, factorise !
if action_type == 'push':
    push_ids = kw.get('push_ids', ())
    level = kw.get('level', None)
    logger.debug("push_ids=%s on level %s", push_ids, level)
    member_ids = kw.get('member_ids', ())
    if not push_ids:
        psm = 'psm_select_at_least_one_item'
        err = 1
    elif level is None:
        psm = 'psm_select_a_level'
        err = 1
    else:
        nb_push = len(push_ids)
        kw['levels'] = nb_push*[level]
        kw['directive'] = nb_push*[kw.get('directive', '')]
        kw['delegation_date'] = nb_push*[DateTime()]
        kw['data_lists'] = ('directive', 'delegation_date',)
        res = wftool.doActionFor(context, workflow_action, **kw)
        psm = 'psm_roadmap_changed'

elif action_type == 'edit':
    logger.debug(action_type)
    # what we want
    dates = ()
    string_data = ('directive', 'user_comment')

    # elements ids
    edit_ids = kw.get('edit_ids', ())
    logger.debug("edit_ids=%s", edit_ids)

    # ensure that we won't destroy elts that might have been otherwise
    # checked...
    kw.pop('pop_ids', ())

    # data extraction
    try:
        date_lists = dict(
            (key, [makeDate(dstr) for dstr in kw['key']])
             for key in dates
             if key in kw)
    except ValueError, err:
        # XXX AT: cannot pass %s to translation
        psm = "Invalid date: ${date (%s)}" % err
        err = 1
    else:
        kw.update(date_lists)

        kw['data_list'] = dates + string_data
        # GR: catch exceptions for user feedback ? Should not happen anyway
        wftool.doActionFor(context, workflow_action, **kw)

elif action_type == 'move_down':
    wftool.doActionFor(context,
                       workflow_actions['move_down'],
                       **kw)
    psm = 'psm_status_changed'

elif action_type == 'pop':
    pop_ids = kw.get('pop_ids', ())
    logger.debug("pop_ids=%s", pop_ids)
    if not pop_ids:
        psm = 'psm_select_at_least_one_item'
        err = 1
    else:
        res = wftool.doActionFor(context, workflow_actions['pop'], **kw)
        psm = 'psm_roadmap_changed'


if REQUEST is not None:
    # if object is not is the same state, do not redirect to the
    # workflow_action_form page but to the object view page because transition
    # names will not be the same in a different state
    page_template = workflow_action_form
    new_state = wftool.getInfoFor(context, 'review_state', None)
    if old_state != new_state:
        page_template = 'view'

    redirect_kws = {
        'workflow_action': workflow_action,
        'current_var_id': current_var_id,
        'portal_status_message': psm,
        }
    # get search kws when redirecting after an error on push
    if err == 1 and action_type == 'push':
        keys = ['search_param', 'search_term']
        for key in keys:
            if kw.has_key(key):
                redirect_kws[key] = kw.get(key)

    redirect_kws = urlencode(redirect_kws)
    redirect_url = '%s/%s?%s' % (context.absolute_url(),
                                 page_template,
                                 redirect_kws)
    REQUEST.RESPONSE.redirect(redirect_url)
else:
    return (res, psm, err)
