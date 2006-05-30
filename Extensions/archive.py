"""Utility script to trigger the archiving of old closed mails

Parameters are set in Products.CPSCourrier.config.py

Add this as External Method to the root of the portal:

    id: archive
    title: whatever
    module: CPSCourrier.archive
    function: archive

"""

from Products.CMFCore.utils import getToolByName
from Products.CPSCourrier.archive import Archiver

def archive(self):
    wftool = getToolByName(self, 'portal_workflow')
    portal = getToolByName(self, 'portal_url').getPortalObject()
    archiver = Archiver(portal)
    return "archived %d mail documents" % archiver.archive()

