# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
# Author: G. Racinet <gracinet@nuxeo.com>
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
"""DgmeRel specific GenericSetup import/export"""

from Products.CMFCore.utils import getToolByName

class VariousImporter(object):

    def __init__(self, context):
        self.context = context
        self.site = context.getSite()
        self.logger = context.getLogger('CPSCourrier Various')

    def importVarious(self):
        """Do import."""
        self.setupInjectorGlobalRole()

    def setupInjectorGlobalRole(self):
        """Add an Injector entry to roles directory."""

        aclu = self.site.acl_users
        dtool = self.site.portal_directories
        rdir = dtool[aclu.roles_dir]
        inj_id = 'Injector'
        if not rdir._hasEntry(inj_id):
            self.logger.info("Creating an Injector entry in roles directory")
            rdir._createEntry({rdir.id_field: inj_id})
        else:
            self.logger.info("Roles dir has an Injector entry. Nothing to do.")

# Called according to import_steps.xml
def importVarious(context):
    importer = VariousImporter(context)
    importer.importVarious()



