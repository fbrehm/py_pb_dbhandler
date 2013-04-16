#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Frank Brehm
@contact: frank.brehm@profitbricks.com
@organization: Profitbricks GmbH
@copyright: © 2010 - 2013 by Profitbricks GmbH
@license: GPL3
@summary: module for a abstract database entity class
          for a PostgreSQL database
"""

# Standard modules
import sys
import os
import re
import logging

from abc import ABCMeta, abstractmethod

# Third party modules

# Own modules
from pb_base.common import pp, to_unicode_or_bust, to_utf8_or_bust

from pb_base.object import PbBaseObjectError
from pb_base.object import PbBaseObject

from pb_base.errors import PbReadTimeoutError, CallAbstractMethodError

from pb_dbhandler import BaseDbError

from pb_dbhandler.translate import translator

_ = translator.lgettext
__ = translator.lngettext

__version__ = '0.1.0'

log = logging.getLogger(__name__)

#==============================================================================
class DbEntityError(BaseDbError, PbBaseObjectError):
    """
    Base error class
    """

    pass

#==============================================================================
class DatabaseEntity(PbBaseObject):
    """
    Abstract base class for a database entity object.
    """

    __metaclass__ = ABCMeta

    entity_name = 'unknown_entity'
    """
    @cvar: a class variable for the table or view name of the entity
    @type: str
    """

    #--------------------------------------------------------------------------
    def __init__(self,
            appname = None,
            verbose = 0,
            version = __version__,
            base_dir = None,
            use_stderr = False,
            initialized = False,
            ):  
        """ 
        Initialisation of the database entity object.

        @raise DbEntityError: on a uncoverable error.

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
        @param initialized: initialisation is complete after __init__()
                            of this object
        @type initialized: bool

        @return: None
        """

        super(DatabaseEntity, self).__init__(
                appname = appname,
                verbose = verbose,
                version = version,
                base_dir = base_dir,
                use_stderr = use_stderr,
                initialized = False,
        )

        self.initialized = True

    #--------------------------------------------------------------------------
    @property
    def name(self):
        """The table or view name of the entity."""
        return self.entity_name

    #--------------------------------------------------------------------------
    @abstractmethod
    def create(self, *args, **kwargs):
        """
        Abstract method to create a new entity.
        Must be overridden in inherited classes.
        """

        raise CallAbstractMethodError(
                self.__class__.__name__,
                'create', *args, **kwargs)

    #--------------------------------------------------------------------------
    @abstractmethod
    def modify(self, *args, **kwargs):
        """
        Abstract method to modify an existing entity.
        Must be overridden in inherited classes.
        """

        raise CallAbstractMethodError(
                self.__class__.__name__,
                'modify', *args, **kwargs)

    #--------------------------------------------------------------------------
    @abstractmethod
    def get(self, *args, **kwargs):
        """
        Abstract method to get the data of an existing entity.
        Must be overridden in inherited classes.
        """

        raise CallAbstractMethodError(
                self.__class__.__name__,
                'get', *args, **kwargs)

    #--------------------------------------------------------------------------
    @abstractmethod
    def remove(self, *args, **kwargs):
        """
        Abstract method to remove an existing entity.
        Must be overridden in inherited classes.
        """

        raise CallAbstractMethodError(
                self.__class__.__name__,
                'create', *args, **kwargs)

#==============================================================================

if __name__ == "__main__":
    pass

#==============================================================================

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4
