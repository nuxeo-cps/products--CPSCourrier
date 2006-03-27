##parameters=form
"""Extract the list of rapths + the transition id from the REQUEST object

This is an helper script for the cpscourrier_batch_perform_form template
"""

data = {}

# Two types of widgets can be used to feed the batch perform script:
# - the catalog tabular widget that directly uses rpaths
# - the folder contents tabular widget that uses ids relative to the current
#   rpath
if 'ids' in form:
    utool = context.portal_url
    folder_rpath = utool.getRpath(context.aq_inner)
    data['rpaths'] = ['%s/%s' % (folder_rpath, id) for id in form['ids']]
else:
    data['rpaths'] = form.get('rpaths', ())

if not data['rpaths']:
    psm = 'psm_select_at_least_one_item'
    url = "%s?portal_status_message=%s" % (context.absolute_url(), psm)
    context.REQUEST.RESPONSE.redirect(url)

PREFIX = "cpscourrier_batch_"
trans = [key for key in form if key.startswith(PREFIX)]
if len(trans) > 1:
    raise ValueError("Got more than one transition")
data['transition'] = trans[0][len(PREFIX):]
return data
