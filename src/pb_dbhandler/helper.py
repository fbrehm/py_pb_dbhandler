#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@profitbricks.com
@organization: Profitbricks GmbH
@copyright: © 2010 - 2013 by Profitbricks GmbH
@license: GPL3
@summary: module for some helper functions
"""

# Standard modules
import sys
import os
import re
import logging

# Third party modules
import argparse

# Own modules
from pb_base.common import pp, to_unicode_or_bust, to_utf8_or_bust

from pb_base.object import PbBaseObjectError

import pb_dbhandler
from pb_dbhandler import default_db_host
from pb_dbhandler import default_db_port
from pb_dbhandler import max_port_number

from pb_dbhandler.translate import translator

_ = translator.lgettext
__ = translator.lngettext

__version__ = '0.1.0'

log = logging.getLogger(__name__)

#==============================================================================
class PortArgparseAction(argparse.Action):

    def __call__(self, parser, namespace, values, option_string = None):

        port = int(values)

        m1 = _("The port number of a PostgreSQL database must be greater than zero.")
        m2 = _("The port number of a PostgreSQL database must be less or equal %d.")

        if port < 1:
            raise argparse.ArgumentError(self, m1)
        if port > max_port_number:
            raise argparse.ArgumentError(self, (m2 % (max_port_number)))

        setattr(namespace, self.dest, port)

#==============================================================================
def init_db_argparser(parser,
        def_db_host = default_db_host,
        def_db_port = default_db_port,
        def_db_schema = None,
        def_db_user = None
    ):
    """
    Init of the typical database options with the given argument parser.

    @param parser: the argument parser object, where to add the database
                   arguments
    @type parser: argparse.ArgumentParser
    @param def_db_host: a hostname or IP address to display as the default
                        database host
    @type def_db_host: str
    @param def_db_port: a TCP port number to display as the default
                        port number of PostgreSQL on the database host.
    @type def_db_port: int
    @param def_db_schema: a name to display as the default database schema.
    @type def_db_schema: str
    @param def_db_user: a name to display as the default database user.
    @type def_db_user: str

    """

    db_group = parser.add_argument_group(_('Database options'))

    h_h = _("The host of the PostgreSQL database (Default: %r).") % (
            def_db_host)
    db_group.add_argument(
            '--db-host', '-H',
            action = "store",
            dest = 'db_host',
            metavar = 'HOST',
            help = h_h,
    )

    h_p = _("The TCP port of PostgreSQL database on the database machine (Default: %d).") % (
            def_db_port)
    db_group.add_argument(
            '--db-port', '-P',
            action = PortArgparseAction,
            dest = 'db_port',
            type = int,
            metavar = 'PORT',
            help = h_p,
    )

    h_s = _("The database schema (database) used on DB host.")
    if def_db_schema:
        h_s = _("The database schema (database) used on DB host (Default: %r).") % (
                def_db_schema)
    db_group.add_argument(
            '--db-schema', '-S',
            action = "store",
            dest = 'db_schema',
            metavar = 'SCHEMA',
            help = h_s,
    )

    h_u = _("The database user using for connecting to DB.")
    if def_db_user:
        h_u = _("The database user using for connecting to DB (Default: %r).") % (
                def_db_user)
    db_group.add_argument(
            '--db-user', '-U',
            action = "store",
            dest = 'db_user',
            metavar = 'USER',
            help = h_u,
    )

    h_pw = _("The password of the database user connecting to DB.")
    h_pw += " " + _("The usage of this parameter is not recommended.")
    h_pw += " " + _("Better use an appropriate entry in the $HOME/.pgpass file.")
    db_group.add_argument(
            '--db-password',
            action = "store",
            dest = 'db_password',
            metavar = 'PASSWORD',
            help = h_pw,
    )

#==============================================================================
def init_db_cfg_spec(spec,
        def_db_host = default_db_host,
        def_db_port = default_db_port,
        def_db_schema = None,
        def_db_user = None
    ):
    """
    Method to complete the initialisation a config
    specification file. It adds some specific configuration options
    for the access to a PostgreSQL database.

    See configobj for the syntax.

    @param spec: The specification object, which should extended.
    @type spec: dict
    @param def_db_host: a hostname or IP address to display as the default
                        database host
    @type def_db_host: str
    @param def_db_port: a TCP port number to display as the default
                        port number of PostgreSQL on the database host.
    @type def_db_port: int
    @param def_db_schema: a name to display as the default database schema.
    @type def_db_schema: str
    @param def_db_user: a name to display as the default database user.
    @type def_db_user: str

    """

    if not u'db' in spec:
        spec[u'db'] = {}
        spec.comments[u'db'].append('')
        spec.comments[u'db'].append('')
        spec.comments[u'db'].append(
                u'Configuration parameters for the database connection')
        spec.comments[u'db'].append(
                u'NOTE: the database password is not included in ' +
                u'the configuration.')
        spec.comments[u'db'].append(
                u'If a password is needed, then it should be ' +
                u'included in a .pgpass file.')

    db_host_spec = u"string(default = '%s')" % (
            to_unicode_or_bust(def_db_host))
    if not u'host' in spec[u'db']:
        spec[u'db'][u'host'] = db_host_spec
        spec[u'db'].comments[u'host'].append('')
        spec[u'db'].comments[u'host'].append(
                u'The hostname or IP address of the PostgreSQL ' +
                u'database server')

    if not u'port' in spec[u'db']:
        spec[u'db'][u'port'] = (u'integer(min = 1, ' +
                u'max = %d, default = %d)') % ((2**15 - 1), def_db_port)
        spec[u'db'].comments[u'port'].append('')
        spec[u'db'].comments[u'port'].append(
                u'The TCP port number of the PostgreSQL database server')

    schema_spec = u"string(default = '%s')" % (
            to_unicode_or_bust(def_db_schema))
    if not u'schema' in spec[u'db']:
        spec[u'db'][u'schema'] = schema_spec
        spec[u'db'].comments[u'schema'].append('')
        spec[u'db'].comments[u'schema'].append(
                u'The DNS database schema of the PostgreSQL ' +
                u'database server')

    user_spec = u"string(default = '%s')" % (
            to_unicode_or_bust(def_db_user))
    if not u'user' in spec[u'db']:
        spec[u'db'][u'user'] = user_spec
        spec[u'db'].comments[u'user'].append('')
        spec[u'db'].comments[u'user'].append(
                u'The DNS database user of the PostgreSQL ' +
                u'database server')

#==============================================================================

if __name__ == "__main__":
    pass

#==============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
