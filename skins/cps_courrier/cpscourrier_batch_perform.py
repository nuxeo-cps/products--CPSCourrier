##parameters=REQUEST=None

# this script is here as a test of buttons. Transform to a view on ICPSProxy
# or IObjectManager

form = REQUEST.form
ids = form.pop('ids', ())
#return str(REQUEST.form)

if len(form) > 1:
    raise ValueError("Got more than one transition")

transition = form.keys()[0]
return "You asked to perform transition %s\nObjects: %s" % (transition,
                                                            ', '.join(ids))
