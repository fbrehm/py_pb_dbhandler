#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@profitbricks.com
@organization: Profitbricks GmbH
@copyright: © 2010 - 2013 by Profitbricks GmbH
@license: GPL3
@summary: base handler module for database handler classes
          with PostgreSQL as database system
"""

# Standard modules
import sys
import os
import os.path
import re
import logging

# Third party modules
import psycopg2

# Own modules
from pb_base.common import pp, to_unicode_or_bust, to_utf8_or_bust

from pb_base.object import PbBaseObjectError
from pb_base.object import PbBaseObject

from pb_base.errors import PbReadTimeoutError

from pb_base.handler import PbBaseHandlerError
from pb_base.handler import CommandNotFoundError
from pb_base.handler import PbBaseHandler

from pb_dbhandler import BaseDbError

import pb_dbhandler.pgpass

from pb_dbhandler.pgpass import default_pgpass_file
from pb_dbhandler.pgpass import PgPassFileError
from pb_dbhandler.pgpass import PgPassFileNotExistsError
from pb_dbhandler.pgpass import PgPassFile

from pb_dbhandler.translate import translator

_ = translator.lgettext
__ = translator.lngettext

__version__ = '0.2.0'

log = logging.getLogger(__name__)

#==============================================================================
class BaseDbHandlerError(BaseDbError, PbBaseHandlerError):
    """
    Base error class
    """

    pass

#==============================================================================
class BaseDbHandler(PbBaseHandler):
    """
    Base class for a object with database connectivity.
    """

    #--------------------------------------------------------------------------
    def __init__(self,
            db_host = 'localhost',
            db_port = 5432,
            db_schema = None,
            db_user = None,
            db_passwd = None,
            connect_params = None,
            auto_connect = False,
            simulate = False,
            pgpass_file = None,
            appname = None,
            verbose = 0,
            version = __version__,
            base_dir = None,
            use_stderr = False,
            sudo = False,
            quiet = False,
            ):
        """
        Initialisation of the base handler object.

        @raise BaseDbError: on an exception on a uncoverable error.

        @param db_host: the host of the PostgreSQL database
        @type db_host: str
        @param db_port: the TCP port of PostgreSQL on the database machine.
        @type db_port: int
        @param db_schema: the database schema using on the DB.
        @type db_schema: str
        @param db_user: the database user using for connecting to DB.
        @type db_user: str
        @param db_passwd: the password of the database user connecting to DB.
        @type db_passwd: str
        @param connect_params: additional connect parameters for connecting
                               to database
        @type connect_params: dict
        @param auto_connect: establish connection at the end of initialization
                             of this object
        @type auto_connect: bool
        @param simulate: don't execute DDL or DMS operations, only display them,
        @type simulate: bool
        @param pgpass_file: a .pgpass file, where the password could be searched,
                            if no password was given.
                            If not given, $HOME/.pgpass will used.
        @type pgpass_file: str
        @type appname: str
        @param verbose: verbose level
        @type verbose: int
        @param version: the version string of the current object or application
        @type version: str
        @param base_dir: the base directory of all operations
        @type base_dir: str
        @param use_stderr: a flag indicating, that on handle_error() the output
                           should go to STDERR, even if logging has
                           initialized logging handlers.
        @type use_stderr: bool
        @param sudo: should the command executed by sudo by default
        @type sudo: bool
        @param quiet: don't display ouput of action after calling
        @type quiet: bool

        @return: None

        """

        # Initialisation of the parent object
        super(BaseDbHandler, self).__init__(
                appname = appname,
                verbose = verbose,
                version = version,
                base_dir = base_dir,
                use_stderr = use_stderr,
                initialized = False,
                simulate = simulate,
                sudo = sudo,
                quiet = quiet,
        )

        self._auto_connect = bool(auto_connect)
        """
        @ivar: establish connection at the end of initialization
               of this object
        @type: bool
        """

        self.connection = None
        """
        @ivar: the connection object for all database operations
        @type: psycopg2.connection
        """

        self.cursor = None
        """
        @ivar: database cursor object for performing actions
        @type: psycopg2.cursor
        """

        self._db_host = db_host
        """
        @ivar: The host of the PostgreSQL database.
        @type: str
        """

        self._db_port = int(db_port)
        """
        @ivar: The TCP port of PostgreSQL on the database machine.
        @type: int
        """

        self._db_schema = db_schema
        """
        @ivar: The database schema (database) used on DB host.
        @type: str
        """

        self._db_user = db_user
        """
        @ivar: The database user using for connecting to DB.
        @type: str
        """

        self._db_passwd = db_passwd
        """
        @ivar: The password of the database user connecting to DB.
        @type: str
        """

        self._connect_params = {}
        """
        @ivar: additional connect parameters for connecting to DB
               see: http://www.postgresql.org/docs/9.1/static/libpq-connect.html#LIBPQ-PQCONNECTDBPARAMS
        @type: dict
        """
        if connect_params and isinstance(connect_params, dict):
            self._connect_params = connect_params

        if self.auto_connect:
            self.connect()

        self._pgpass_file = pgpass_file
        """
        @ivar: a .pgpass file, where the password could be searched,
               if no password was given.
        @type: str
        """

        self.initialized = True

    #------------------------------------------------------------
    @property
    def auto_connect(self):
        """Establish connection at the end of initialization"""
        return getattr(self, '_auto_connect', False)

    @auto_connect.setter
    def auto_connect(self, value):
        self._auto_connect = bool(value)

    #------------------------------------------------------------
    @property
    def connected(self):
        """Is this object currently connected with database?"""
        connection = getattr(self, 'connection', None)
        if not connection:
            return False
        if connection.closed:
            return False
        return True

    #------------------------------------------------------------
    @property
    def cursor_opened(self):
        """Is there currently an open cursor on the database?"""
        cursor = getattr(self, 'cursor', None)
        if not cursor:
            return False
        if cursor.closed:
            return False
        return True

    #------------------------------------------------------------
    @property
    def db_host(self):
        """The host of the PostgreSQL database."""
        return self._db_host

    #------------------------------------------------------------
    @property
    def db_port(self):
        """The TCP port of PostgreSQL on the database machine."""
        return self._db_port

    #------------------------------------------------------------
    @property
    def db_schema(self):
        """The database schema (database) used on DB host."""
        return self._db_schema

    #------------------------------------------------------------
    @property
    def db_user(self):
        """The database user using for connecting to DB."""
        return self._db_user

    #------------------------------------------------------------
    @property
    def db_passwd(self):
        """The password of the database user connecting to DB."""
        return self._db_passwd

    #------------------------------------------------------------
    @property
    def connect_params(self):
        """
        Additional connect parameters for connecting to DB.
        See: http://www.postgresql.org/docs/9.1/static/libpq-connect.html#LIBPQ-PQCONNECTDBPARAMS
        """
        return self._connect_params

    #------------------------------------------------------------
    @property
    def pgpass_file(self):
        """
        A .pgpass file, where the password could be searched,
        if no password was given.
        If not given, $HOME/.pgpass will used.
        """

        return self._pgpass_file

    #--------------------------------------------------------------------------
    def as_dict(self, short = False):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(BaseDbHandler, self).as_dict(short = short)

        res['db_host'] = self.db_host
        res['db_port'] = self.db_port
        res['db_schema'] = self.db_schema
        res['db_user'] = self.db_user
        res['connect_params'] = self.connect_params
        res['pgpass_file'] = self.pgpass_file
        res['auto_connect'] = self.auto_connect
        res['connected'] = self.connected
        res['cursor_opened'] = self.cursor_opened
        if self.db_passwd is None:
            res['db_passwd'] = None
        else:
            res['db_passwd'] = '**********'

        if not res['pgpass_file']:
            res['pgpass_file'] = default_pgpass_file

        return res

    #--------------------------------------------------------------------------
    def __repr__(self):
        """Typecasting into a string for reproduction."""

        out = super(BaseDbHandler, self).__repr__()[:-2]

        fields = []
        if self.db_host:
            fields.append("db_host=%r" % (self.db_host))
        if self.db_port:
            fields.append("db_port=%r" % (self.db_port))
        if self.db_schema:
            fields.append("db_schema=%r" % (self.db_schema))
        if self.db_user:
            fields.append("db_user=%r" % (self.db_user))
        if self.db_passwd:
            fields.append("db_passwd=%r" % (self.db_passwd))
        if self.connect_params:
            fields.append("connect_params=%r" % (self.connect_params))
        if self.auto_connect:
            fields.append("auto_connect=%r" % (self.auto_connect))

        if fields:
            out += ', ' + ", ".join(fields)
        out += ")>"
        return out

    #--------------------------------------------------------------------------
    def __del__(self):
        """
        Destructor.
        No parameters, no return value.
        """

        if self.verbose > 1:
            log.debug(_("Destroying base database object."))
        self.close()

    #--------------------------------------------------------------------------
    def check_password(self):
        """
        Checks the existence of the password.
        If no password was given (self.db_passwd is None), then the password
        will searched in the .pgpass file. If nothing was found, an empty
        password will used.
        """

        if self.db_passwd is not None:
            return

        pgpass = None

        try:
            pgpass = PgPassFile(
                    filename = self.pgpass_file,
                    appname = self.appname,
                    base_dir = self.base_dir,
                    use_stderr = self.use_stderr,
                    verbose = self.verbose,
            )
        except PgPassFileError, e:
            log.warn(_("Error performing .pgpass file, using empty password: %s"), e)
            self._db_passwd = ''
            return

        password = pgpass.get_passwd(
                hostname = self.db_host, port = self.db_port,
                database = self.db_schema, username = self.db_user
        )

        self._db_passwd = password
        return

    #--------------------------------------------------------------------------
    def connect(self):
        """
        Establish a connection with the PostgreSQL database.
        """

        if self.connection and not self.connection.closed:
            msg = _("Trying to establish a connection while an existing " +
                    "database connection.")
            raise BaseDbError(msg)

        self.check_password()

        c_params = {}
        c_params['host'] = self._db_host
        if self._db_port and self._db_port != 5432:
            c_params['port'] = self._db_port
        c_params['database'] = self._db_schema
        c_params['user'] = self._db_user
        c_params['password'] = self._db_passwd
        for key in self._connect_params:
            c_params[key] = self._connect_params[key]

        log.debug(_("Used parameters to connect to database:") + "\n%s",
                pp(c_params))

        connection = psycopg2.connect(**c_params)
        self.connection = connection
        if self.simulate:
            log.debug(_("Setting DB connection to readonly."))
            self.connection.set_session(readonly = True)

    #--------------------------------------------------------------------------
    def open_cursor(self):
        """
        Tries to open a cursor in the database
        Saves this cursor in self.cursor
        """

        if self.verbose > 3:
            log.debug(_("DB connection: %r"), self.connection)
            if self.connection:
                if self.connection.closed:
                    log.debug(_("DB connection closed."))
                else:
                    log.debug(_("DB connection opened."))
            log.debug(_("DB cursor: %r"), self.cursor)

        if not self.connected:
            raise BaseDbError(_("Not connected to database."))

        if self.cursor:
            self.close_cursor()

        if self.verbose > 1:
            log.debug(_("Opening database cursor."))

        self.cursor = self.connection.cursor()

    #--------------------------------------------------------------------------
    def close_cursor(self):
        """
        Closes the current cursor.
        """

        if not self.connected:
            del self.cursor
            self.cursor = None
            return

        if not self.cursor:
            return

        if self.verbose > 1:
            log.debug(_("Closing database cursor."))

        if not self.cursor.closed:
            self.cursor.close()

        del self.cursor
        self.cursor = None

        return

    #--------------------------------------------------------------------------
    def close(self):
        """
        Close the database connection.
        """

        self.close_cursor()

        if self.connection:
            if not self.connection.closed:
                log.debug(_("Closing the database connection."))
                self.connection.close()
            if self.verbose > 2:
                log.debug(_("Destroying db connection object."))
            del self.connection
            self.connection = None

#==============================================================================

if __name__ == "__main__":
    pass

#==============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
