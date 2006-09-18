
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

"""Directory Related Widgets (for Paper setup)
"""
from Globals import InitializeClass
from Acquisition import aq_parent, aq_inner, aq_base

from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.Widget import widgetRegistry
from Products.CPSSchemas.Widget import CPSWidget
from Products.CPSSchemas.Widget import widgetname
from Products.CPSSchemas.BasicWidgets import renderHtmlTag
from Products.CPSSchemas.BasicWidgets import CPSProgrammerCompoundWidget
from Products.CPSSchemas.BasicWidgets import CPSSelectWidget


class CPSDirectoryMultiIdWidget(CPSProgrammerCompoundWidget):
    """A widget that makes ids from multiple sources.

    The first field is the target field, it gets composed from the other
    ones, that are in principle managed by subwidgets"""

    meta_type = "Directory Multi Id Widget"
    _properties = CPSProgrammerCompoundWidget._properties + (
        {'id': 'ldap_syntax', 'type': 'boolean', 'mode': 'w',
         'label': 'Use ldap dn syntax?'},
        {'id': 'ldap_renamings', 'type': 'boolean', 'mode': 'w',
         'label': 'Ldap dn renaming (<field id>:<dn part>, comma separated). Does not apply to rdn'},
        )

    ldap_syntax = False
    ldap_renamings = ''
    render_method = 'widget_directory_multi_id_render'

    def _getPrepareValidateMethod(self):
        """Override. Called from CPSProgrammerCompondWidget."""
        return self.prepare_validate

    def prepare_validate(self, action, datastructure):
        """prepare or validate datastructure."""

        if action in ['prepare', 'prevalidate']:
            return
        elif action != 'validate':
            raise ValueError(action)

        dm = datastructure.getDataModel()
        id_field = self.fields[0]
        layout = aq_parent(aq_inner(self))
        subfields = self.fields[1:]
        if self.ldap_syntax:
            if self.ldap_renamings:
                mapping = dict(mapp.strip().split(':')
                               for mapp in self.ldap_renamings.strip().split(','))
            else:
                mapping = {}
            items = ['%s=%s' % (mapping.get(field_id, field_id), dm[field_id])
                     for field_id in subfields[1:]]
            items.insert(0, dm[subfields[0]])
        else:
            items = [dm[field_id] for field_id in subfields]

        dm[self.fields[0]] = ','.join(items)
        return True


InitializeClass(CPSDirectoryMultiIdWidget)
widgetRegistry.register(CPSDirectoryMultiIdWidget)

class CPSPaperMailRecipientWidget(CPSWidget):
    """ A select with links to directories.

    Dispatch to two widgets that *must* share the same field with this one.
    """

    render_method = 'widget_paper_mail_recipient_render'
    meta_type = 'Paper Mail Recipient Widget'
    _properties = CPSWidget._properties + (
        {'id': 'widget_local_id', 'type': 'string', 'mode': 'w',
         'label': 'Sub widget for local directory'},
        {'id': 'widget_global_id', 'type': 'string', 'mode': 'w',
         'label': 'Sub widget for global directory'},
        {'id': 'widget_internal_id', 'type': 'string', 'mode': 'w',
         'label': 'Sub widget for internal recipient directory'},
        )

    widget_local_id = ''
    widget_global_id = ''
    widget_internal_id = ''

    def prepare(self, ds, **kw):
        dm = ds.getDataModel()

        value = dm[self.fields[0]]
        if isinstance(value, list):
            value = value and value[0] or ''
        if value.startswith('local:'):
            value = value[6:]
            ds[self.widget_local_id] = value
            ds[self.widget_global_id] = ''
            ds[self.widget_internal_id] = ''
            ds[self.getWidgetId()+ '_is_local'] = True # for render()
        elif value.startswith('global:'):
            value = value[7:]
            ds[self.widget_local_id] = ''
            ds[self.widget_internal_id] = ''
            ds[self.widget_global_id] = value
        elif value.startswith('internal:'):
            value = value[9:]
            ds[self.widget_local_id] = ''
            ds[self.widget_internal_id] = value
            ds[self.widget_global_id] = ''
            ds[self.getWidgetId()+ '_is_internal'] = True # for render()
        else:
            # useful mostly for init
            ds[self.widget_local_id] = ds[self.widget_global_id] = ds[self.widget_internal_id] = value

    def validate(self, ds, **kw):
        dm = ds.getDataModel()
        field_id = self.fields[0]
        use_lists = isinstance(dm[self.fields[0]], list)

        local_v = ds.get(self.widget_local_id)
        global_v = ds.get(self.widget_global_id)
        internal_v = ds.get(self.widget_internal_id)

        # select appropriate subwidget
        if local_v and global_v and not internal_v:
            ds.setError(self.getWidgetId(),
                        "Vous ne pouvez choisir dans les deux annuaires simultan\xe9ment")
            return False
        elif internal_v:
            wid = self.widget_internal_id
        elif local_v:
            wid = self.widget_local_id
        else: # global_v by default, say
            wid = self.widget_global_id

        # let the subwidget validate
        layout = self.aq_inner.aq_parent
        widget = layout[wid]
        ok = widget.validate(ds, **kw)

        # putting right prefixes
        if local_v:
            dm[field_id] = 'local:%s' % dm[field_id]
        elif internal_v:
            dm[field_id] = 'internal:%s' % dm[field_id]
        else:
            dm[field_id] = 'global:%s' % dm[field_id]
        if use_lists:
            dm[field_id] = [dm[field_id]]

        return True

    def render(self, mode, datastructure, **kw):
        # need to ensure that we prepare after subwidgets preparation
        # this is ugly, I'd prefer to change layout.prepareLayoutWidgets
        # to check on _forbidden_widgets.
        self.prepare(datastructure)
        meth = getattr(self, self.render_method, None)
        if meth is None:
            msg = "Unknown Render Method %s for widget type %s. " \
            + "Please set or change the 'render_method' attribute on " \
            + "your widget declaration."
            raise RuntimeError(msg % (self.render_method, self.getId()))

        layout = aq_parent(aq_inner(self))
        if mode in ['edit', 'create']:
            # global/local vs internal will be controlled by visibility expr
            # in subwidgets config
            widget_ids = (self.widget_global_id, self.widget_local_id,
                          self.widget_internal_id)

            # GR big copy/paste from CPSCompoundWidget. Subclassing would be
            # better, and better to make subwidgets generic. Another time

            cells = []
            widget_infos = kw['widget_infos']
            for widget_id in widget_ids:
                cell = {}
                # widget, widget_mode, css_class
                cell.update(widget_infos[widget_id])
                widget = layout[widget_id]
                widget_mode = cell['widget_mode']
                if widget_mode == 'hidden':
                    continue
                rendered = widget.render(widget_mode, datastructure, **kw)
                rendered = rendered.strip()
                cell['widget_rendered'] = rendered
                if not widget.hidden_empty or rendered:
                    # do not add widgets to be hidden when empty
                    cells.append(cell)
            return meth(mode=mode, datastructure=datastructure,
                        cells=cells, **kw)
            # end C/P
        elif mode == 'view':
            wid = self.getWidgetId()
            if datastructure.get(wid+'_is_local'):
                widget = layout[self.widget_local_id]
            elif datastructure.get(wid+'_is_internal'):
                widget = layout[self.widget_internal_id]
            else:
                widget = layout[self.widget_global_id]
            return widget.render(mode, datastructure, **kw)



InitializeClass(CPSPaperMailRecipientWidget)
widgetRegistry.register(CPSPaperMailRecipientWidget)


class CPSDirectoryLinkSelectWidget(CPSSelectWidget):
    """Select widget rendering with links to a directory according to mode.

    CPSCourrier specifics lie in the creation links:
       - pick ou from the parent
       - fetch in the url for form prefill
    This could become configurable. Link part should be a subwidget actually
    """

    meta_type = "Directory Link Select Widget"

    _properties = CPSSelectWidget._properties + (
        {'id': 'directory', 'type': 'string', 'mode': 'w',
         'label': 'Directory to link to'},
        {'id': 'skip_prepare', 'type': 'boolean', 'mode': 'w',
         'label': 'Skip preparation (you know what you are doing)'},
        {'id': 'create_form_prefill', 'type': 'boolean', 'mode': 'w',
         'label': 'Prefill popup with value of ou field from parent'}
        )

    directory = ''
    skip_prepare = False
    create_form_prefill = False

    def prepare(self, ds, **kw):
        # no need (and harmul) to prepare if subwidget of
        # Paper Mail Recipient Widget
        if not self.skip_prepare:
            return CPSSelectWidget.prepare(self, ds, **kw)

    def render(self, mode, ds, **kw):
        base_url = getToolByName(self, 'portal_url').getBaseUrl()
        dtool_url = '%sportal_directories/%s' % (base_url, self.directory)
        vocabulary = self._getVocabulary(ds)
        value = ds[self.getWidgetId()]
        if mode == 'view':
            if self.translated:
                cpsmcat = getToolByName(self, 'translation_service')
                contents = cpsmcat(vocabulary.getMsgid(value, value)).encode('ISO-8859-15', 'ignore')
            else:
                contents = vocabulary.get(value, value)
            href = '%s/cpsdirectory_entry_view?dirname=%s&id=%s' % (
                dtool_url,
                self.directory,
                value)
            return renderHtmlTag('a', href=href, contents=contents)

        base_render = CPSSelectWidget.render(self, mode, ds, **kw)

        ## Now add a link to create form if perms are ok

        # get ou
        ou = None
        if self.create_form_prefill:
            proxy = ds.getDataModel().getProxy()
            if proxy is not None:
                mbox = aq_parent(aq_inner(proxy))
                if mbox.portal_type == 'Mailbox':
                    ou = mbox.getContent().ou

        #  check perms
        dtool = getToolByName(self, 'portal_directories')
        dir_ = dtool[self.directory]
        if not dir_.isCreateEntryAllowed({'ou':ou}):
            return base_render

        # render
        cpsmcat = getToolByName(self, 'translation_service')
        contents = cpsmcat('cpscourrier_new_addressbook_entry').encode(
            self.default_charset)

        args_base = 'dirname=%s' % self.directory
        if self.create_form_prefill:
            args_base += '&%s=%s' % (widgetname('mailbox'), ou)
        href = '%s/cpsdirectory_entry_create_form?%s' % (dtool_url, args_base)
        args_popup = args_base + '&formaction=cpscourrier_popup_entry_create_form'
        href_popup = '%s/cpscourrier_popup_entry_create_form?%s' % (dtool_url,
                                                                    args_popup)

        onclick = "window.open('%s', 'Entry Create', 'location=0,toolbar=0,width=640,height=480,resizable=1;dependent=1');return false" % href_popup
        link_render = renderHtmlTag('a', href=href,
                                    contents=contents, onclick=onclick)

        return '\n'.join((base_render, link_render))

InitializeClass(CPSDirectoryLinkSelectWidget)
widgetRegistry.register(CPSDirectoryLinkSelectWidget)
