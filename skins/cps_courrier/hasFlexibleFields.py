##parameters=data

"""Tell if the data comes from an object's datamodel and the object has
flexible field"""


import re
regexp = '_f[0..9]+$'

return int(bool([fid for fid in data if re.search(regexp, fid) is not None]))
