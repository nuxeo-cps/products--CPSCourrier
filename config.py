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
"""Some CPSCourrier-specific parameters

If ZMI edition + XML I/O for those parameters is needed, we might write a simple
portal_cpscourrier tool with an XMLAdapter to hosts those parameters as
properties.
"""

# Id of the relation graph that will host CPSCourrier relations between mails
# and their responses
RELATION_GRAPH_ID = "cpscourrier"

# Outgoing Mail -> Incoming Mail relation id (one to one)
IS_REPLY_TO = 'is_reply_to'

# Incoming Mail -> Outgoing Mail relation id (one to many)
HAS_REPLY = 'has_reply'

# Id of the workflow stack
STACK_ID = 'Pilots'


