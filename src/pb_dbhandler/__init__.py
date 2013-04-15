#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@profitbricks.com
@copyright: © 2010 - 201r32 by Frank Brehm, Berlin
@summary: All modules used by database handler stuff
"""

import os
import sys

# Own modules

from pb_base.object import PbBaseObjectError

__author__ = 'Frank Brehm <frank.brehm@profitbricks.com>'
__copyright__ = '(C) 2010-2013 ProfitBricks GmbH, Berlin'
__contact__ = 'frank.brehm@profitbricks.com'
__version__ = '0.4.3'
__license__ = 'GPL3'

default_db_host = 'localhost'
default_db_port = 5432
max_port_number = 2**15 - 1

#==============================================================================
class BaseDbError(PbBaseObjectError):
    """
    Base error class for all exceptions belonging
    to the database handler stuff
    """

    pass

#==============================================================================

if __name__ == "__main__":

    pass

#==============================================================================

# vim: fileencoding=utf-8 filetype=python ts=4
