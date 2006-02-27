# -*- encoding: iso-8859-15 -*-
#$Id$

# A script to make a default cps dev site
# modified to use CPSCourrier extension profile





import transaction
from AccessControl.SecurityManagement import newSecurityManager
from Testing.makerequest import makerequest

app = makerequest(app)

print "Creating root user"
aclu = app.acl_users
aclu._addUser('root','root','root', ['Manager', 'Owner'], [])

transaction.commit()

print "Loging in as root user"
user = aclu.getUserById('root').__of__(aclu)
newSecurityManager(None, user)

print "Adding CPS Site..." # doesn't work cf #1381

app.manage_addProduct['CPSDefault'].addConfiguredCPSSite(
    site_id='cps',
    title='CPS Dev Site',
    manager_id='manager',
    password='manager',
    password_confirm='manager',
    manager_email='gracinet@nuxeo.com',
    manager_lastname='CPS Manager',
    languages=['fr', 'en'],
    profile_id='CPSDefault:default',
    extension_ids=('CPSCourrier:default',)
    )

# create some mailboxes & groups

mailboxes = app.cps.mailboxes
wftool = mailboxes.portal_workflow

grp1_id = wftool.invokeFactoryFor(mailboxes, 'Mailbox Group', 'mailbox_grp_1',
                                  Title='Groupe un')
grp2_id = wftool.invokeFactoryFor(mailboxes, 'Mailbox Group', 'mailbox_grp_2',
                                  Title='Groupe deux')
grp1 = getattr(mailboxes, grp1_id)
grp2 = getattr(mailboxes, grp2_id)

mbox1 = wftool.invokeFactoryFor(grp1, 'Mailbox', 'mbox1',
                               Title='Boîte fonctionnelle')
mbox2 = wftool.invokeFactoryFor(grp2, 'Mailbox', 'mbox2',
                                Title='Boîte en plus')

# create some users
mdir = app.cps.portal_directories.members
entries = [{'id': 'test%d' % i,
            'sn': 'Test %d' %i,
            'fullname' : 'Test user %d' %i,
            'givenName' : 'User',
            'userPassword' : 'test'}
           for i in range(5)]

for entry in entries:
    mdir._createEntry(entry)


transaction.commit()
