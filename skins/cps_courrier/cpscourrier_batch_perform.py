##parameters=REQUEST=None

# this script is here as a test of buttons. Transform to a view on ICPSProxy
# or IObjectManager

form = REQUEST.form
list_ids = ('ids', 'rpaths',)
refs = ()
for l_id in list_ids:
    vals = form.pop(l_id, ())
    if not refs:
        refs = vals
        name = l_id

PREFIX = "cpscourrier_batch_"
trans = [key for key in form if key.startswith(PREFIX)]
if len(trans) > 1:
    raise ValueError("Got more than one transition")

transition = trans[0][len(PREFIX):]
return "You asked to perform transition '%s'\n%s: %s" % (transition,
                                                       name,
                                                       ', '.join(refs))
