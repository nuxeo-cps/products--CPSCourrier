# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
# Author: Georges Racinet <gracinet@nuxeo.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA
# 02111-1307, USA.
#
# $Id$

from Products.CPSSchemas.DataModel import DataModel

class FakeBrain:
    """ A pseudo brain out of a dict (for tests) """
    def __init__(self, d):
        for key, item in d.items():
            setattr(self, key, item)

class BrainDataModel(DataModel):
    """ To use brain catalog results as a datamodel.

    Proof-of-concept level implementation.

    >>> d = FakeBrain({'spam': 'eggs', 'a': 'b'})
    >>> dm =  BrainDataModel(d)
    >>> dm._brain == d
    True
    >>> dm['spam']
    'eggs'
    >>> dm['non']
    Traceback (most recent call last):
    ...
    KeyError: 'non'
    >>> dm['non'] = 0
    Traceback (most recent call last):
    ...
    NotImplementedError
    """

    def __init__(self, brain):
        self._brain = brain

    def getObject(self):
        meth = getattr(self._brain, 'getObject', None)
        if meth is None:
            return self._brain
        else:
            return meth()

    def __getitem__(self, key):
        try:
            return getattr(self._brain, key)
        except AttributeError:
            raise KeyError(key)

    def __setitem__(self, key, item):
        raise NotImplementedError


