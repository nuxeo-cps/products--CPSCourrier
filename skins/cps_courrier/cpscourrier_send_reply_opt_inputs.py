##parameters=
#$Id$

inputs = []
cpsmcat = context.translation_service
charset = context.default_charset

# submit as template
inputs.append({'type': 'checkbox',
               'name': 'submit_template',
               'label': cpsmcat('cpscourrier_submit_template').encode(charset)})

return inputs
