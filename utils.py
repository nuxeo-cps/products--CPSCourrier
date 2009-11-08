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

#$Id$

import base64

import re

from Products.CMFCore.utils import getToolByName
from Products.CPSSkins import minjson as json
from Products.CPSUtil.text import toAscii
from Products.CPSSchemas.BasicWidgets import CPSFileWidget

def hasFlexibleFields(data):
    """True if the passed dict looks like a datamodel with flexible fields.

    Was used in write expression for 'has_attachment' field
    """

    regexp = '_f[0..9]+$'

    # XXX GR the 'and' close shouldn't be necessary, but there are
    # empty flexible fields in some of our mails
    # also bool on iterators doesn't check non emptiness

    return int(bool([fid for fid in data
                     if re.search(regexp, fid) and data[fid] is not None]))

def hasVisibleFlexibleWidget(doc):
    """True if the passed CPSDocument instance has a visible flexible widget.

    Used in write expression for 'has_attachment' field. Hidden widgets would
    correspond to embedded images.
    Normally, the flexible widget and fields are created at once, by means
    of addFlexibleWidget method of FlexibleTypeInformation.

    This returns an integer instead of a boolean, in order to be compatible
    with all indexing solutions.
    """

    try:
        layout, _ = doc.getTypeInfo()._getFlexibleLayoutAndSchemaFor(
            doc, 'mail_flexible')
    except AttributeError: # no flexible layout or schema
        return 0
    for widget in layout.objectValues():
        if not isinstance(widget, CPSFileWidget):
            continue
        if not 'view' in widget.hidden_layout_modes: # not hidden
            return 1
    return 0


# based on CPSSkins versions, but can handle non ascii-chars
# here not to break possible CPSSkins assumptions

# XXX since we eventually patched both, we could settle for utf8, which
# json.read seems to assume by default
def serializeForCookie(obj, charset='ascii'):
    """Convert a python data structure into a base64 encoded string suitable
    for storing in a cookie."""

    string = json.write(obj)
    # base64 will cast to str, producing Unicode errors
    if isinstance(string, unicode):
        string = string.encode(charset)
    v = base64.encodestring(string)
    return v.replace('\n', '') # cookie values cannot contain newlines

def unserializeFromCookie(string='', default=None, charset='ascii'):
    """Convert a base64 string into a python object"""

    value = default
    if not string:
        return value

    # If not already unicode, myjson will try to decode assuming utf-8
    v = base64.decodestring(string).decode(charset)
    try:
        value = json.read(v)
    except IndexError:
        pass

    return value


def createOuInLDAP(ldir, ou):
    """Create a new ou in given ldap backing directory."""

    dn = 'ou=%s,%s' % (ou, ldir.ldap_base_creation)
    attrs = {'objectClass': ['top', 'organizationalUnit'],
             'ou': ou}
    ldir.insertLDAP(dn, attrs)

def computeMailboxOu(portal, title):
    """Compute an unique ou for a new mailbox.

    >>> class FakePortal:
    ...      existing = []
    ...      def portal_catalog(self, ou=None):
    ...          if ou in self.existing:
    ...               return[ou]
    ...          return []
    >>> portal = FakePortal()
    >>> portal.existing = ['spam', 'bacon']
    >>> portal.portal_catalog(ou='spam')
    ['spam']

    >>> computeMailboxOu(portal, 'truc')
    'truc'
    >>> ou = computeMailboxOu(portal, 'spam')
    >>> print ou; portal.existing.append(ou)
    spam_1
    >>> ou = computeMailboxOu(portal, 'spam')
    >>> print ou; portal.existing.append(ou)
    spam_2
    >>> computeMailboxOu(portal, 'bacon')
    'bacon_1'
    """

    catalog = portal.portal_catalog

    current = cleaned = toAscii(title).lower()
    i = 1
    existing = True
    while existing:
        existing = catalog(ou=current)
        if not existing:
            break
        current = '%s_%d' % (cleaned, i)
        i += 1
    dtool = getToolByName(portal, 'portal_directories', None)
    if dtool is not None: # not in unit tests
        ldir = getattr(dtool, 'local_addressbook_ldap', None)
        if ldir is not None:
            createOuInLDAP(ldir, current)
    return current
