#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author: Frank Brehm
@contact: frank.brehm@profitbricks.com
@organization: Profitbricks GmbH
@copyright: © 2010 - 2013 by Profitbricks GmbH
@license: GPL3
@summary: test script (and module) for unit tests on the PgPassFile class
'''

import unittest
import os
import sys
import logging
import tempfile
import stat

libdir = os.path.abspath(os.path.join(os.path.dirname(sys.argv[0]), '..', 'src'))
sys.path.insert(0, libdir)

import general
from general import DbHandlerTestcase, get_arg_verbose, init_root_logger

import pb_base.object
from pb_base.object import PbBaseObjectError

from pb_base.common import pp

import pb_dbhandler
from pb_dbhandler import BaseDbError

import pb_dbhandler.pgpass
from pb_dbhandler.pgpass import PgPassFileError
from pb_dbhandler.pgpass import PgPassFileNotExistsError
from pb_dbhandler.pgpass import PgPassFileNotReadableError
from pb_dbhandler.pgpass import PgPassFile

log = logging.getLogger(__name__)

#==============================================================================
class TestPgPassFile(DbHandlerTestcase):

    #--------------------------------------------------------------------------
    def setUp(self):
        self.pgpassfile = os.path.join(os.path.dirname(sys.argv[0]), '.pgpass')
        self.pgpassfile_fail = os.path.join(
                os.path.dirname(sys.argv[0]), '.pgpass-bliblablub')

    #--------------------------------------------------------------------------
    def test_pgpass_object(self):

        log.info("Testing init of a PgPassFile object.")

        log.debug("Default .pgpass file: %r",
                pb_dbhandler.pgpass.default_pgpass_file)

        pgpass = PgPassFile(filename = self.pgpassfile, verbose = self.verbose)
        if self.verbose > 2:
            log.debug("PgPassFile object:\n%s", pgpass)
        self.assertIsInstance(pgpass, PgPassFile)
        pgpassfile_real = os.path.realpath(self.pgpassfile)
        self.assertEqual(pgpass.filename, pgpassfile_real)

        with self.assertRaises(PgPassFileNotExistsError) as cm:
            pgpass = PgPassFile(filename = self.pgpassfile_fail,
                    verbose = self.verbose)
        e = cm.exception
        log.debug("%s raised on not existing .pgpass file %r: %s",
                'PgPassFileNotExistsError', self.pgpassfile_fail, e)

    #--------------------------------------------------------------------------
    def test_read_pgpass(self):

        (fd, filename) = tempfile.mkstemp()
        os.write(fd, 'bla\n')
        os.close(fd)
        mode = stat.S_IRUSR | stat.S_IWUSR
        log.debug("Changing permissions of %r to %o.", filename, mode)
        os.chmod(filename, mode)

        try:
            log.info("Testing reading of a .pgpass file.")
            pgpass = PgPassFile(filename = filename, verbose = self.verbose)
            content = pgpass.read()
            log.debug("Got file content of %r: %r", filename, content)
            self.assertIsInstance(content, basestring)
            self.assertEqual(content, 'bla\n')

            mode = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH
            log.debug("Changing permissions of %r to %o.", filename, mode)
            os.chmod(filename, mode)
            content = pgpass.read()
            log.debug("Got file content of %r: %r", filename, content)
            self.assertIsInstance(content, basestring)
            self.assertEqual(content, '')

            log.debug("Reading in force mode ...")
            pgpass = PgPassFile(filename = filename,
                    verbose = self.verbose,
                    force = True)
            content = pgpass.read()
            log.debug("Got file content of %r: %r", filename, content)
            self.assertIsInstance(content, basestring)
            self.assertEqual(content, 'bla\n')

        finally:
            if os.path.exists(filename):
                os.remove(filename)

    #--------------------------------------------------------------------------
    def test_parse_entries1(self):

        (fd, filename) = tempfile.mkstemp()
        os.write(fd, 'localhost:5432:*:glassfish:ov4Lael3ugoh\n')
        os.write(fd, '# bla bla\n')
        os.write(fd, 'app1:5432:*:glassfish:ov4Lael3ugoh\n')
        os.write(fd, '\n')
        os.close(fd)
        mode = stat.S_IRUSR | stat.S_IWUSR
        os.chmod(filename, mode)

        try:

            log.info("Testing parsing of a normal .pgpass file.")
            pgpass = PgPassFile(filename = filename, verbose = self.verbose)

            entries = pgpass.entries()
            if self.verbose > 2:
                l = []
                for e in entries:
                    l.append(e.as_dict(True))
                log.debug("Got entries:\n%s", pp(l))

            self.assertEqual(len(entries), 2)

        finally:
            if os.path.exists(filename):
                os.remove(filename)

    #--------------------------------------------------------------------------
    def test_parse_entries2(self):

        (fd, filename) = tempfile.mkstemp()
        os.write(fd, 'localhost:5432:\n')
        os.write(fd, '# bla bla\n')
        os.write(fd, 'app1:5432tt:*:glassfish:ov4Lael3ugoh\n')
        os.write(fd, '\n')
        os.close(fd)
        mode = stat.S_IRUSR | stat.S_IWUSR
        os.chmod(filename, mode)

        try:

            log.info("Testing parsing of a corrupt .pgpass file.")
            pgpass = PgPassFile(filename = filename, verbose = self.verbose)

            entries = pgpass.entries()
            if self.verbose > 2:
                log.debug("Got entries:\n%r", entries)

            self.assertEqual(len(entries), 0)

        finally:
            if os.path.exists(filename):
                os.remove(filename)

    #--------------------------------------------------------------------------
    def test_parse_entries3(self):

        (fd, filename) = tempfile.mkstemp()
        os.write(fd, 'local\\host:5432:*:glass\\:fish:ov:La\\:nel3::oh\n')
        os.close(fd)
        mode = stat.S_IRUSR | stat.S_IWUSR
        os.chmod(filename, mode)

        try:

            log.info("Testing parsing of a .pgpass file with escaped fields.")
            pgpass = PgPassFile(filename = filename, verbose = self.verbose)

            entries = pgpass.entries()
            if self.verbose > 2:
                log.debug("Got entries:\n%r", entries)

            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].hostname, r'local\host')
            self.assertEqual(entries[0].port, 5432)
            self.assertEqual(entries[0].database, None)
            self.assertEqual(entries[0].username, r'glass:fish')
            self.assertEqual(entries[0].password, r'ov:La:nel3::oh')

        finally:
            if os.path.exists(filename):
                os.remove(filename)

    #--------------------------------------------------------------------------
    def test_get_passwd(self):

        (fd, filename) = tempfile.mkstemp()
        os.write(fd, 'app:5432:vdc:glassfish:passwd1\n')
        os.write(fd, 'app:5432:*:glassfish:passwd2\n')
        os.write(fd, 'app:5432:*:uhu:passwd3\n')
        os.write(fd, 'app:5432:*:*:passwd4\n')
        os.write(fd, 'app:5434:*:glassfish:passwd5\n')
        os.write(fd, 'localhost:5432:*:glassfish:passwd6\n')
        os.close(fd)
        mode = stat.S_IRUSR | stat.S_IWUSR
        os.chmod(filename, mode)

        try:

            log.info("Testing parsing of a .pgpass file with escaped fields.")
            pgpass = PgPassFile(filename = filename, verbose = self.verbose)

            pwd = pgpass.get_passwd(
                    hostname = 'app', port = 5432, database = 'vdc',
                    username = 'glassfish'
            )
            self.assertEqual(pwd, 'passwd1')

            pwd = pgpass.get_passwd(
                    hostname = 'app', port = 5432, database = 'bla',
                    username = 'glassfish'
            )
            self.assertEqual(pwd, 'passwd2')

            pwd = pgpass.get_passwd(
                    hostname = 'app', port = 5432, database = 'vdc',
                    username = 'uhu'
            )
            self.assertEqual(pwd, 'passwd3')

            pwd = pgpass.get_passwd(
                    hostname = 'app', port = 5432, database = 'bla',
                    username = 'uhu'
            )
            self.assertEqual(pwd, 'passwd3')

            pwd = pgpass.get_passwd(
                    hostname = 'app', port = 5432, database = 'bla',
                    username = 'itsme'
            )
            self.assertEqual(pwd, 'passwd4')

            pwd = pgpass.get_passwd(
                    hostname = 'app', port = 5434, database = 'bla',
                    username = 'glassfish'
            )
            self.assertEqual(pwd, 'passwd5')

            pwd = pgpass.get_passwd(
                    hostname = 'app', port = 5434, database = 'bla',
                    username = 'itsme'
            )
            self.assertEqual(pwd, None)

            pwd = pgpass.get_passwd(
                    hostname = 'localhost', port = 5432, database = 'bla',
                    username = 'glassfish'
            )
            self.assertEqual(pwd, 'passwd6')

            pwd = pgpass.get_passwd(
                    hostname = 'localhost', port = 5432, database = 'bla',
                    username = 'itsme'
            )
            self.assertEqual(pwd, None)

            pwd = pgpass.get_passwd(
                    hostname = 'somewhere', port = 5432, database = 'bla',
                    username = 'glassfish'
            )
            self.assertEqual(pwd, None)


        finally:
            if os.path.exists(filename):
                os.remove(filename)

#==============================================================================


if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    log.info("Starting tests ...")

    suite = unittest.TestSuite()

    suite.addTest(TestPgPassFile('test_pgpass_object', verbose))
    suite.addTest(TestPgPassFile('test_read_pgpass', verbose))
    suite.addTest(TestPgPassFile('test_parse_entries1', verbose))
    suite.addTest(TestPgPassFile('test_parse_entries2', verbose))
    suite.addTest(TestPgPassFile('test_parse_entries3', verbose))
    suite.addTest(TestPgPassFile('test_get_passwd', verbose))

    runner = unittest.TextTestRunner(verbosity = verbose)

    result = runner.run(suite)


#==============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
