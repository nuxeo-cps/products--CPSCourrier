##parameters=data

"""Tell if the data comes from an object's datamodel and the object has
flexible field"""


import re
regexp = '_f[0..9]+$'

# XXX GR the 'and' close shouldn't be necessary, but there are empty flexible
# fields in some of our mails
# also bool on iterators doesn't check non emptiness
return int(bool([fid for fid in data
                 if re.search(regexp, fid) and data[fid] is not None]))
