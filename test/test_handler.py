#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''
@author: Frank Brehm
@contact: frank.brehm@profitbricks.com
@organization: Profitbricks GmbH
@copyright: © 2010 - 2013 by Profitbricks GmbH
@license: GPL3
@summary: test script (and module) for unit tests on the BaseDbHandler class
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
from pb_dbhandler.pgpass import default_pgpass_file

import pb_dbhandler.handler
from pb_dbhandler.handler import BaseDbHandlerError
from pb_dbhandler.handler import BaseDbHandler

log = logging.getLogger(__name__)

#==============================================================================
class TestBaseDbHandler(DbHandlerTestcase):

    #--------------------------------------------------------------------------
    def setUp(self):
        self.db_host = 'app1.dc1.de.profitbricks.net'
        self.db_port = 5432
        self.db_schema = 'vdc'
        self.db_user = 'glassfish'
        pass

    #--------------------------------------------------------------------------
    def test_dbhandler_object(self):

        log.info("Testing init of a BaseDbHandler object.")

        log.debug("Default .pgpass file: %r", default_pgpass_file)

        dbhandler = BaseDbHandler(
                db_host = self.db_host,
                db_port = self.db_port,
                db_schema = self.db_schema,
                db_user = self.db_user,
                verbose = self.verbose,
        )

        if self.verbose > 2:
            log.debug("BaseDbHandler object:\n%s", dbhandler)
        self.assertIsInstance(dbhandler, BaseDbHandler)
        self.assertEqual(dbhandler.connected, False)
        self.assertEqual(dbhandler.cursor_opened, False)
        del dbhandler

    #--------------------------------------------------------------------------
    def test_dbhandler_checkpw(self):

        log.info("Testing check_password() of a BaseDbHandler object.")

        log.debug("Using .pgpass file: %r", default_pgpass_file)

        dbhandler = BaseDbHandler(
                db_host = self.db_host,
                db_port = self.db_port,
                db_schema = self.db_schema,
                db_user = self.db_user,
                verbose = self.verbose,
        )

        dbhandler.check_password()
        self.assertIsNotNone(dbhandler.db_passwd)
        if not os.path.exists(default_pgpass_file):
            self.assertEqual(dbhandler.db_passwd, '')

        del dbhandler

    #--------------------------------------------------------------------------
    def test_dbhandler_connect(self):

        log.info("Testing connect() of a BaseDbHandler object.")
        if not os.path.exists(default_pgpass_file):
            log.warn("File %r doesn't exists, cannot check connect().",
                    default_pgpass_file)
            return

        dbhandler = BaseDbHandler(
                db_host = self.db_host,
                db_port = self.db_port,
                db_schema = self.db_schema,
                db_user = self.db_user,
                verbose = self.verbose,
        )

        dbhandler.connect()
        if self.verbose > 2:
            log.debug("BaseDbHandler object:\n%s", dbhandler)
        self.assertEqual(dbhandler.connected, True)
        self.assertEqual(dbhandler.cursor_opened, False)

        del dbhandler

#==============================================================================


if __name__ == '__main__':

    verbose = get_arg_verbose()
    if verbose is None:
        verbose = 0
    init_root_logger(verbose)

    log.info("Starting tests ...")

    suite = unittest.TestSuite()

    suite.addTest(TestBaseDbHandler('test_dbhandler_object', verbose))
    suite.addTest(TestBaseDbHandler('test_dbhandler_checkpw', verbose))
    suite.addTest(TestBaseDbHandler('test_dbhandler_connect', verbose))

    runner = unittest.TextTestRunner(verbosity = verbose)

    result = runner.run(suite)


#==============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
