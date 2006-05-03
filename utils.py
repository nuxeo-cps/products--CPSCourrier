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


import re

def hasFlexibleFields(data):
    """True if the passed dict looks like a datamodel with flexible fields.

    Used in write expression for 'has_attachment' field
    """

    regexp = '_f[0..9]+$'

    # XXX GR the 'and' close shouldn't be necessary, but there are
    # empty flexible fields in some of our mails
    # also bool on iterators doesn't check non emptiness

    return int(bool([fid for fid in data
                     if re.search(regexp, fid) and data[fid] is not None]))
