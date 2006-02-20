# A script to make a default cps dev site





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

transaction.commit()
