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

from Products.CMFCore.utils import getToolByName

from Products.CPSSchemas.DataModel import DataModel

class FakeBrain:
    """ A pseudo brain out of a dict (for tests) """
    def __init__(self, d):
        for key, item in d.items():
            setattr(self, key, item)

class BrainDataModel(DataModel):
    """ To use brain catalog results as a datamodel.

    This is basically an indirection to the brains attributes, plus some
    computed ones (url etc.).
    XXX GR leverage schema/adapters and use a regular datamodel ?

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
        self._forbidden_widgets = []
        self._brain = brain
        self.data = {}

    def getObject(self):
        meth = getattr(self._brain, 'getObject', None)
        if meth is None:
            return self._brain
        else:
            return meth()

    def __getitem__(self, key):
        # If already computed, return value
        value = self.data.get(key)
        if value is not None:
            return value

        # fallback to brain attribute
        try:
            value = getattr(self._brain, key)
        except AttributeError:
            # try and compute some values (see XXX in docstring for improvement)
            brain = self._brain
            if key == 'rpath':
                utool = getattr(self, 'utool', None)
                if utool is None:
                     utool = getToolByName(self._brain, 'portal_url')
                     self.utool = utool
                value = utool.getRpathFromPath(brain.getPath())
            elif key == 'url':
                rpath = self.__getitem__('rpath')
                # we are now sure that self.utool has been set
                value = self.utool.getUrlFromRpath(rpath)
            else:
                raise KeyError(key)

        self.data[key] = value
        return value

    def __setitem__(self, key, item):
        raise NotImplementedError


