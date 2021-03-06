CPS Courrier
============

Mail tracking and management system for CPS Platform.

Dependencies
------------

 - CPS >= 3.4.1
 - CPSRelation
 - CPSBayes
 - BayesCore and it's denpendencies (SQLObject and TextIndexNG3 extensions)

Installation
------------

 - add this product and its dependencies to the ``Products`` directory of your Zope instance.
 - (re)start Zope
 - Select ``CPSCourrier Site`` in the ``Add`` menu and fill the form

Traps
~~~~~

 - Lucene external indexing: several CPSCourrier sites can't share a
   Lucene server.

Usage
-----

This product creates a new document root "Mailboxes" as the root of the portal
that holds all the mail boxes of the portal. You can create new mailboxes by
using the `New` action. Mailboxes can get organized into "Groups of mailboxes"
to manage access rights for several mailboxes.

Users can create new 'Dashboards' documents in their homefolder. A dashboard is
a document that display the filtered result of a query.

Technical Overview
------------------

CPS Courrier is an extension profile for the CPSDefault base profiles that
brings the following:

  - new document types: "Mailbox Group", "Mailbox", "In"/"Outgoing mail and
    Dashboards
  - new (stack-based) workflow chains for the mail documents. This WF chains are
    set available in the root of Mailboxes.
  - a new powerful Tabular Widget to display the result of queries as
    configurable tables that are built from a layout of atomic widgets (one for
    each column).

CPSCourrier uses a CPSRelation graph to store the relations between incoming and
ougoing mail documents (replies). By default this uses the IOBTree (ZODB)
storage but it can be setup to store the relations in some RDF graph in a MySQL
database.

