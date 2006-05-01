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

"""Specific widgets that have nothing to do with tabular widgets.
"""
from Globals import InitializeClass
from Acquisition import aq_parent, aq_inner

from Products.CPSSchemas.Widget import widgetRegistry
from Products.CPSSchemas.Widget import CPSWidget
from Products.CPSSchemas.BasicWidgets import renderHtmlTag
from Products.CPSSchemas.BasicWidgets import CPSSelectWidget

class CPSMailTopicsWidget(CPSSelectWidget):
    """Aggregate default topics from mailbox together with stored ones.

    Parent's field holding topics must have the same id as the current object's
    """

    meta_type = "Mail Topics Widget"

    def validate(self, datastructure, **kw):
        """Validate datamodel from datastructure.

        Does not check validity, because there's no fixed referential."""

        dm = datastructure.getDataModel()
        dm[self.fields[0]] = datastructure[self.getWidgetId()]
        return True

    def getParentTopics(self, datastructure):
        """return the list of topics attached to the parent.

        Typically, the parent is a mailbox."""

        dm = datastructure.getDataModel()
        proxy = dm.getProxy()
        if proxy is None:
            return []
        if proxy is not None:
            parent = aq_parent(aq_inner(proxy)).getContent()
            return getattr(parent, self.fields[0], [])

    def renderInputDiv(self, topic, voc, checked=False, css_class=None, cpsmcat=None):
        """make a <div> holding a checkbox and label."""

        if css_class is not None:
            start = '<div class=%s>' % css_class
        else:
            start = '<div>'
        end = '</div>'
        name = self.getHtmlWidgetId()
        checkbox_id = '%s-%s' % (name,topic)
        checkbox = renderHtmlTag('input',
                                 type='checkbox',
                                 name='%s:list' % name,
                                 checked=checked and 'checked' or None,
                                 id=checkbox_id)

        # 'for' is a python reserved word
        if cpsmcat is not None:
            contents = cpsmcat(voc.getMsgid(topic, topic), 'ignore').encode(
                'iso-8859-15')
        else:
            contents = voc.get(topic, topic)
        label = renderHtmlTag('label', **{'for':checkbox_id, 'contents': contents})
        return '\n'.join((start,checkbox,label,end))

    def render(self, mode, datastructure, **kw):
        """render in mode from datastructure.

        Highlights topics that don't come from the mailbox."""
        topics = datastructure[self.getWidgetId()]
        parent_topics = self.getParentTopics(datastructure)
        if self.translated:
            cpsmcat = getToolByName(self, 'translation_service')
        else:
            cpsmcat = None
        input_name = self.getHtmlWidgetId()
        outstanding_topics = [topic for topic in topics if topic not in parent_topics]
        voc = self._getVocabulary(datastructure)
        rendered_topics = [self.makeInputDiv(topic, voc,
                                             css_class='outstanding',
                                             cpsmcat=cpsmcat,
                                             checked=True)
                           for topic in outstanding_topics]
        for topic in parent_topics:
            rendered_topics.append(self.makeInputDiv(topic, voc, cpsmcat=cpsmcat,
                                                     checked=topic in topics))
        return '\n'.join(rendered_topics)

InitializeClass(CPSMailTopicsWidget)
widgetRegistry.register(CPSMailTopicsWidget)
