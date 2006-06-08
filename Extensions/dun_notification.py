"""This External Method finds all mail documents that have not been
processed in time and notifies LocalManagers and Supervisors about them
by sending a simple email.


How to use it:
   Create an ExternalMethod at the root of portal with
          Id: dun_notify
          Module Name: CPSCourrier.dun_notification
          Function Name: notify

   You can then put (on *nix platforms) a wget call of the following type in
   a cron job:
   $ wget --http-user=<user> --http-passwd=<pwd> <portal_url>/dun_notify

   The given user must have the Manager global role

   VIRTUAL HOSTING:

   If you are in a virtual hosting context, you have to call the same base
   URL as the one your users access to, otherwise people will get useless links
   in the produced emails.

   I18N WITH WGET

   To choose the language in which the email messages have to be translated,
   use the --header option of wget, as in
   wget --header='Accept-Language: fr' ...

   In doubts, check what your favorite browser sends in its browser when
   accessing the portal under the wished language
"""

from Products.CMFCore.utils import getToolByName

from Products.CPSCourrier.dun import DunNotifier
from Products.CPSCourrier.workflows.scripts import HTML_BODY_WRAPPER

def notify(self):
    portal = getToolByName(self, 'portal_url').getPortalObject()

    notifier = DunNotifier(portal)
    notifier.date_tolerance = -1

    report = notifier.notify()
    report_str = ["Notified %d person(s) about %s documents in mailbox at %s" % (

        len(info['notifiees']), info['late_number'], info['mb_url'])
                  for info in report]

    body = "<h1>Notification reminder for late mail documents</h1>"
    "<h2>Report</h2>"
    body += '<br/>'.join(report_str)
    return HTML_BODY_WRAPPER % body
