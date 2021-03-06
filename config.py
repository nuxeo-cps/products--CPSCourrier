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

# CPSRelation resources can be prefixed to avoid namespace polution on RDF
# based backends
RELATION_PREFIX = 'cpscourrier'

# Incoming Mail -> Outgoing Mail relation id (one to many)
HAS_REPLY = 'has_reply'

# Minimum probability to flag a mail with a subject
BAYES_MIN_PROB = 0.7

# Id of the workflow stack
STACK_ID = 'Pilots'

# FS directory name in to host the archives
ARCHIVE_HOME = "$INSTANCE_HOME/var/archive"
ARCHIVE_HOME = ARCHIVE_HOME.replace("$INSTANCE_HOME", INSTANCE_HOME)

# Minimum number of days for mails to get archived
ARCHIVE_MIN_AGE = 60

# Mappping of incoming -> outgoing for replies
REPLY_PTYPE_MAPPING = {
    'Incoming Email': 'Outgoing Email',
    'Incoming Pmail': 'Outgoing Pmail',
    }
