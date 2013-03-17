#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from distutils.core import setup, Command

# own modules:
cur_dir = os.getcwd()
if sys.argv[0] != '' and sys.argv[0] != '-c':
    cur_dir = os.path.dirname(sys.argv[0])

libdir = os.path.join(cur_dir, 'src')
pkg_dir = os.path.join(libdir, 'pb_dbhandler')
init_py = os.path.join(pkg_dir, '__init__.py')
if os.path.isdir(pkg_dir) and os.path.isfile(init_py):
    sys.path.insert(0, os.path.abspath(libdir))
del init_py
del pkg_dir
del libdir
del cur_dir

import pb_dbhandler

packet_version = pb_dbhandler.__version__

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = 'pb-dbhandler',
    version = packet_version,
    description = 'ProfitBricks database handler modules',
    long_description = read('README.txt'),
    author = 'Frank Brehm',
    author_email = 'frank.brehm@profitbricks.com',
    url = 'ssh://git.profitbricks.localdomain/srv/git/python/pb-dbhandler.git',
    license = 'LGPLv3+',
    platforms = ['posix'],
    package_dir = {'': 'src'},
    packages = [
        'pb_dbhandler',
    ],
    classifiers = [
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    requires = [
        'pb_base (>= 0.3.10)',
        'psycopg2',
    ]
)

#========================================================================

# vim: fileencoding=utf-8 filetype=python ts=4 expandtab
