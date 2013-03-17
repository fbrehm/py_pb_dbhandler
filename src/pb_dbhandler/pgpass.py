#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@profitbricks.com
@organization: Profitbricks GmbH
@copyright: © 2010 - 2013 by Profitbricks GmbH
@license: GPL3
@summary: Module for reading and searching in $HOME/.pgpass files
"""

# Standard modules
import sys
import os
import stat
import logging
import re
import glob

from gettext import gettext as _

# Third party modules

# Own modules
from pb_base.common import pp, to_unicode_or_bust, to_utf8_or_bust

from pb_base.object import PbBaseObjectError
from pb_base.object import PbBaseObject

from pb_base.errors import PbReadTimeoutError

from pb_base.handler import PbBaseHandlerError
from pb_base.handler import CommandNotFoundError
from pb_base.handler import PbBaseHandler

from pb_dbhandler import BaseDbError

__version__ = '0.1.0'

log = logging.getLogger(__name__)

#---------------------------------------------
# Some module variables

default_pgpass_file = None
try:
    default_pgpass_file = os.path.abspath(os.path.join(
            os.environ['HOME'], '.pgpass'))
except KeyError, e:
    log.error(_("Environment variable %r not set."), 'HOME')
    default_pgpass_file = '.pgpass'

#==============================================================================
class PgPassFileError(BaseDbError):
    """Base error class for all exceptions in this module."""

    pass

#==============================================================================
class PgPassFileNotExistsError(PgPassFileError):
    """Special exception raised, if the .pgpass file doesn't exists."""

    #--------------------------------------------------------------------------
    def __init__(self, filename):
        """
        Constructor.

        @param filename: the name of the missing .pgpass file
        @type filename: str

        """

        self.filename = filename

    #--------------------------------------------------------------------------
    def __str__(self):
        """
        Typecasting into a string for error output.
        """

        return _("Pgpassfile %s doesn't exists.") % (self.filename)

#==============================================================================
class PgPassFileNotReadableError(PgPassFileError):
    """Special exception raised, if the .pgpass s not readable."""

    #--------------------------------------------------------------------------
    def __init__(self, filename):
        """
        Constructor.

        @param filename: the name of the unreadable .pgpass file
        @type filename: str

        """

        self.filename = filename

    #--------------------------------------------------------------------------
    def __str__(self):
        """
        Typecasting into a string for error output.
        """

        return _("Pgpassfile %s is not readable.") % (self.filename)

#==============================================================================
class PgPassEntry(PbBaseObject):
    """
    Encapsulation class for one valid line in a .pgpass file.
    """

    #--------------------------------------------------------------------------
    def __init__(self,
            hostname = None,
            port = None,
            database = None,
            username = None,
            password = '',
            appname = None,
            verbose = 0,
            version = __version__,
            base_dir = None,
            use_stderr = False,
            ):
        """
        Initialisation of the PgPassEntry object.

        @param hostname: the hostname or IP address of the PostGreSQL server
        @type hostname: str or None
        @param port: the TCP port of the PostGreSQL server
        @type port: int or None
        @param database: the database name on the PostGreSQL server
        @type database: str or None
        @param username: the username to use to connetct to the PostGreSQL server
        @type username: str or None
        @param password: the password to use to connetct to the PostGreSQL server
        @type password: str or None
        @param appname: name of the current running application
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

        """

        super(PgPassEntry, self).__init__(
                appname = appname,
                verbose = verbose,
                version = version,
                base_dir = base_dir,
                use_stderr = use_stderr,
                initialized = False,
        )

        self._hostname = hostname
        self._port = None
        if port is not None:
            self._port = int(port)
        self._database = database
        self._username = username
        self._password = password

        self.initialized = True

    #------------------------------------------------------------
    @property
    def hostname(self):
        """The hostname or IP address of the PostGreSQL server."""
        return getattr(self, '_hostname', None)

    #------------------------------------------------------------
    @property
    def port(self):
        """The TCP port of the PostGreSQL server."""
        return getattr(self, '_port', None)

    #------------------------------------------------------------
    @property
    def database(self):
        """The database name on the PostGreSQL server."""
        return getattr(self, '_database', None)

    #------------------------------------------------------------
    @property
    def username(self):
        """The username to use to connetct to the PostGreSQL server."""
        return getattr(self, '_username', None)

    #------------------------------------------------------------
    @property
    def password(self):
        """The password to use to connetct to the PostGreSQL server."""
        return getattr(self, '_password', None)

    #--------------------------------------------------------------------------
    def as_dict(self, short = False):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(PgPassEntry, self).as_dict(short = short)

        res['hostname'] = self.hostname
        res['port'] = self.port
        res['database'] = self.database
        res['username'] = self.username
        res['password'] = self.password

        return res

    #--------------------------------------------------------------------------
    def __repr__(self):
        """Typecasting into a string for reproduction."""

        out = super(PgPassEntry, self).__repr__()[:-2]

        fields = []
        if self.hostname:
            fields.append("hostname=%r" % (self.hostname))
        if self.port:
            fields.append("port=%r" % (self.port))
        if self.database:
            fields.append("database=%r" % (self.database))
        if self.username:
            fields.append("username=%r" % (self.username))
        fields.append("password=%r" % (self.password))

        if fields:
            out += ', ' + ", ".join(fields)
        out += ")>"
        return out

    #--------------------------------------------------------------------------
    def match(self, hostname, port, database, username):
        """
        Checks, whether the given parameters are matching the current
        PgPassEntry object.

        @param hostname: the hostname or IP address of the PostGreSQL server
        @type hostname: str or None
        @param port: the TCP port of the PostGreSQL server
        @type port: int or None
        @param database: the database name on the PostGreSQL server
        @type database: str or None
        @param username: the username to use to connetct to the PostGreSQL server
        @type username: str or None

        @return: the given parameters are matching the current object or not.
        @rtype: bool

        """

        port = int(port)

        if self.hostname is not None:
            if self.hostname.lower() != hostname.lower():
                return False

        if self.port is not None:
            if self.port != port:
                return False

        if self.database is not None:
            if self.database.lower() != database.lower():
                return False

        if self.username is not None:
            if self.username.lower() != username.lower():
                return False

        return True

#==============================================================================
class PgPassFile(PbBaseHandler):
    """
    Encapsulation class of the .pgpass file.
    """

    #--------------------------------------------------------------------------
    def __init__(self,
            filename = None,
            force = False,
            appname = None,
            verbose = 0,
            version = __version__,
            base_dir = None,
            use_stderr = False,
            *targs,
            **kwargs
            ):
        """
        Initialisation of the PgPassFile object.

        @raise CommandNotFoundError: if some needed commands could not be found.
        @raise PgPassFileError: on a uncoverable error.

        @param filename: the filename of the .pgpass file
        @type filename: str
        @param force: use the given .pgpass file, even if it has the wrong permissions
        @type force: bool
        @param appname: name of the current running application
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

        @return: None

        """

        super(PgPassFile, self).__init__(
                appname = appname,
                verbose = verbose,
                version = version,
                base_dir = base_dir,
                use_stderr = use_stderr,
                initialized = False,
                simulate = False,
                sudo = False,
                quiet = False,
        )

        self._filename = None
        """
        @ivar: the filename of the .pgpass file
        @type: None (if not even discoverd) or str
        """

        if filename is None:
            filename = default_pgpass_file

        if not os.path.exists(filename):
            raise PgPassFileNotExistsError(filename)
        self._filename = os.path.realpath(filename)

        self._force = bool(force)
        """
        @ivar: use the given .pgpass file, even if it has the wrong permissions
        @type: bool
        """

        self.initialized = True

    #------------------------------------------------------------
    @property
    def filename(self):
        """The name of the .pgpass file"""
        return getattr(self, '_filename', None)

    #------------------------------------------------------------
    @property
    def force(self):
        """Use the given .pgpass file, even if it has the wrong permissions."""
        return getattr(self, '_force', False)

    #--------------------------------------------------------------------------
    def as_dict(self, short = False):
        """
        Transforms the elements of the object into a dict

        @param short: don't include local properties in resulting dict.
        @type short: bool

        @return: structure as dict
        @rtype:  dict
        """

        res = super(PgPassFile, self).as_dict(short = short)

        res['filename'] = self.filename
        res['force'] = self.force

        return res

    #--------------------------------------------------------------------------
    def __repr__(self):
        """Typecasting into a string for reproduction."""

        out = super(PgPassFile, self).__repr__()[:-2]

        fields = []
        fields.append("filename=%r" % (self.filename))
        fields.append("force=%r" % (self.force))

        if fields:
            out += ', ' + ", ".join(fields)
        out += ")>"
        return out

    #--------------------------------------------------------------------------
    def read(self):
        """
        Read the contents of the .pgpass file. If the .pgpass file has not
        the correct permissions (no permissions for group and others) and force
        is not set, then an empty string is returned.

        @raise PgPassFileNotExistsError: if the .pgpass file doesn't exists
        @raise PgPassFileNotReadableError: if the .pgpass file is not readable
        @raise PgPassFileError: on other errors reading the file

        @return: the file content of the .pgpass file
        @rtype: str
        """

        if not os.path.exists(self.filename):
            raise PgPassFileNotExistsError(self.filename)
        if not os.access(self.filename, os.R_OK):
            raise PgPassFileNotReadableError(self.filename)

        fstat = os.stat(self.filename)
        mode = fstat.st_mode
        user_mode = mode & stat.S_IRWXU
        group_mode = mode & stat.S_IRWXG
        other_mode = mode & stat.S_IRWXO

        if group_mode or other_mode:
            msg = ''
            if not group_mode:
                msg = _("Others have permissions on %r.") % (self.filename)
            elif not other_mode:
                msg = _("Group has permissions on %r.") % (self.filename)
            else:
                msg = _("Group and others have permissions on %r.") % (self.filename)
            if self.force:
                log.debug(msg)
            else:
                log.warn(msg)
                return ''

        return self.read_file(self.filename)

    #--------------------------------------------------------------------------
    def entries(self):
        """
        Reads the .pgpass file and tries to create a list of PgPassEntry
        objects of this.

        @raise PgPassFileError: on parsing errors

        @return: all found entries
        @rtype: list of PgPassEntry

        """

        content = self.read()
        result = []
        if not content:
            if self.verbose > 2:
                log.debug(_("No valid content in %r found."), self.filename)
            return result

        re_comment = re.compile(r'^#')
        re_fields = re.compile(r'(?<!\\):')
        row_nr = 0

        for line in content.splitlines():
            row_nr += 1
            line = line.strip()
            if not line:
                continue
            if re_comment.search(line):
                continue

            hostname = None
            port = None
            database = None
            username = None
            password = None

            fields = re_fields.split(line, 4)
            if self.verbose > 3:
                log.debug(_("Got fields: %r"), fields)
            if not len(fields) == 5:
                msg = _("Invalid entry %(entry)r in %(file)r line %(rownum)d found, only %(nr)d fields found instead of 5.") % {
                        'entry': line, 'file': self.filename,
                        'rownum': row_nr, 'nr': len(fields)}
                log.warn(msg)
                continue

            if fields[0] != '*':
                hostname = fields[0].replace('\\\\', '\\').replace('\\:', ':')
            if fields[1] != '*':
                try:
                    port = int(fields[1])
                except ValueError, e:
                    msg = _("Invalid port %(port)r in %(file)r line %(rownum)d found.") % {
                            'port': fields[1], 'file': self.filename, 'rownum': row_nr}
                    log.warn(msg)
                    continue
            if fields[2] != '*':
                database = fields[2].replace('\\\\', '\\').replace('\\:', ':')
            if fields[3] != '*':
                username = fields[3].replace('\\\\', '\\').replace('\\:', ':')
            password = fields[4].replace('\\\\', '\\').replace('\\:', ':')

            entry = PgPassEntry(
                    hostname = hostname,
                    port = port,
                    database = database,
                    username = username,
                    password = password,
                    appname = self.appname,
                    verbose = self.verbose,
                    base_dir = self.base_dir,
                    use_stderr = self.use_stderr,
            )

            result.append(entry)

        return result

    #--------------------------------------------------------------------------
    def get_passwd(self, hostname, port, database, username):
        """
        Searching the .pgpass file for the given parameters and gives back
        the passord for this entry.

        @param hostname: the hostname or IP address of the PostGreSQL server
        @type hostname: str or None
        @param port: the TCP port of the PostGreSQL server
        @type port: int or None
        @param database: the database name on the PostGreSQL server
        @type database: str or None
        @param username: the username to use to connetct to the PostGreSQL server
        @type username: str or None

        @return: the found password for these entries, or None, if not found
        @rtype: str or None

        """

        passwd = None

        entries = self.entries()
        if self.verbose > 3:
            l = []
            for entry in entries:
                d = entry.as_dict(True)
                d['password'] = '*********'
                l.append(d)
            log.debug(_("Found entries in %(file)r:\n%(list)s") % {
                    'file': self.filename, 'list': pp(l)})

        for entry in entries:
            if entry.match(hostname = hostname, port = port,
                    database = database, username = username):
                passwd = entry.password
                break

        if self.verbose > 2:
            if passwd is not None:
                msg = _("Password found for host %(host)r, port %(port)d, database %(db)r and user %(usr)r.")
            else:
                msg = _("No password found for host %(host)r, port %(port)d, database %(db)r and user %(usr)r.")
            msg = msg % {'host': hostname, 'port': port, 'db': database, 'usr': username}
            log.debug(msg)

        return passwd


#==============================================================================

if __name__ == "__main__":

    pass

#==============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
