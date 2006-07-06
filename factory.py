# (C) Copyright 2006 Nuxeo SAS <http://nuxeo.com>
# Author: G. Racinet <gracinet@nuxeo.com>
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
"""CPSCourrier site factory."""

from Products.CPSDefault.metafactory import CPSSiteMetaConfigurator

#
# Callables for meta profiles
#

def upgradeCatalog(site, **kw):
    """Upgrade the catalog tool to Lucene"""
    from Products.CPSLuceneCatalog.upgrade import upgrade_340_cmf_catalog
    upgrade_340_cmf_catalog(site)


class CPSCourrierSiteConfigurator(CPSSiteMetaConfigurator):
     """ CPS Courrier configurator.
     """

     meta_profiles = {
         'CourrierBase': {'title' : 'Common set of components',
                          'extensions': ('CPSSubscriptions:default',
                                         'CPSSubscriptions:fr',
                                         'CPSDashboards:default',
                                         'CPSCourrier:default',
                                         'CPSCourrier:standalone',
                                         ),
                          'optional' : False,
                          'parameters' : {'attributes': ('smtp_host',
                                                         'smtp_port',
                                                         'smtp_pwd',
                                                         'smtp_uid'),
                                          'class': 'Products.MailHost.'
                                                   'MailHost.MailHost',
                                          'rpath' : 'MailHost'},
                          },

         'CourrierEmail': {'title': 'E-mail handling specifics',
                   'extensions': ('CPSCourrier:email',),
                   'optional': True,
                   },
         'CourrierPaper': {'title': 'Paper mail handling specifics',
                   'extensions': ('CPSCourrier:paper',),
                   'optional': True,},
         }

     metas_order = ('CourrierBase', 'CourrierEmail', 'CourrierPaper',)
     form_heading = "Add CPSCourrier Site"
     post_action = 'addConfiguredCPSCourrierSite'

_cpsconfigurator = CPSCourrierSiteConfigurator()

# GR: straight from CPSDefault.factory
# Do the following dance because bound methods don't play well with
# constructors registered for products.

def addConfiguredCPSCourrierSiteForm(dispatcher):
    """Form to add a CPS Site from ZMI.
    """
    return _cpsconfigurator.addConfiguredSiteForm(dispatcher)

def addConfiguredCPSCourrierSite(dispatcher, REQUEST=None, **kw):
    """Add a CPSSite according to profile and extensions.
    """
    if REQUEST is not None:
        kw.update(REQUEST.form)
    return _cpsconfigurator.addConfiguredSite(dispatcher,
                                              REQUEST=REQUEST, **kw)
