"""Utility script to trigger the archiving of old closed mails

Parameters are set in Products.CPSCourrier.config.py

Add this as External Method to the root of the portal:

    id: archive
    title: whatever
    module: CPSCourrier.archive
    function: archive

To run it in a cron job each night at 2h12, add something along those lines in
your cron tab. Be sure to adjust the user/passwd to some Manager account::

  12 2 * * * /usr/bin/wget -http-user=<user> --http-passwd=<pwd> <portal_url>/archive >/dev/null 2>&1 &
"""

from Products.CMFCore.utils import getToolByName
from Products.CPSCourrier.archive import Archiver

def archive(self):
    wftool = getToolByName(self, 'portal_workflow')
    portal = getToolByName(self, 'portal_url').getPortalObject()
    archiver = Archiver(portal)
    return "archived %d mail documents" % archiver.archive()

