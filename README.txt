CPS Courrier
============

Mail tracking and management system for CPS Platform.

Installation
------------

- install CPS 3.4 and create a `CPS Default Site`
- add this product to the `Products` directory of your Zope instance and restart
  Zope
- In the ZMI, in your CPS instance, goto to the `portal_setup` and select the
  "Profiles" tab
- Select "CPS Courier" and "Import all steps" on the "Import" tab
- that's it

Usage
-----

This product creates a new document root "Mailboxes" as the root of the portal
that holds all the mail boxes of the portal. You can create new mailboxes by
using the `New` action. Mailboxes can get organized into "Groups of mailboxes"
to manage access rights for several mailboxes.

Users have a new management interface on their mailboxes from their home folder.

Technical Overview
------------------

CPS Courrier is an extension profile for the CPSDefault base profiles that
brings the following:

  - new document types: "Mailbox Group", "Mailbox" and "In"/"Outgoing mail
  - new portlets to manage mailboxes
  - new (stack-based) workflow chains
