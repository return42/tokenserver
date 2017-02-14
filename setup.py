#!/usr/bin/env python
# -*- coding: utf-8; mode: python -*-

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.

import re, os
import codecs
from setuptools import setup, find_packages

def read_file(fname):
    with codecs.open(fname, 'r', 'utf-8') as f:
        return f.read()

def find_meta(meta):
    """
    Extract __*meta*__ from META_FILE.
    """
    meta_match = re.search(
        r"^__{meta}__\s*=\s*['\"]([^'\"]*)['\"]".format(meta=meta),
        META_FILE
        , re.M )
    if meta_match:
        return meta_match.group(1)
    raise RuntimeError("Unable to find __{meta}__ string.".format(meta=meta))

NAME = 'tokenserver'

REQUIRES = ['cornice'
            , 'gevent'
            , 'pyramid'
            , 'pyzmq'
            , 'requests'
            , 'SQLAlchemy'
            , 'zope.interface'
            , 'Paste'
            , 'PasteDeploy'
            , 'PasteScript'
            , 'mozsvc>=2.0.0rc1'
            , 'PyBrowserID>=2.0.0rc1'
            ]

EXTRAS_REQUIRE = {}

ENTRY_POINTS="""
[paste.app_factory]
main = tokenserver:main
"""

META_FILE        = read_file(NAME + os.sep + '__init__.py')
LONG_DESCRIPTION = [ read_file(n) for n in ['README.md', 'CHANGES.txt']]

setup(name                   = NAME
      , version              = find_meta('version')
      , description          = find_meta('description')
      , long_description     = '\n\n'.join(LONG_DESCRIPTION)
      , url                  = find_meta('url')
      , author               = find_meta('author')
      , author_email         = find_meta('author_email')
      , license              = find_meta('license')
      , keywords             = find_meta('keywords')
      , packages             = find_packages()
      , include_package_data = True
      , install_requires     = REQUIRES
      , extras_require       = EXTRAS_REQUIRE
      , test_suite           = NAME
      , zip_safe             = False
      , entry_points         = ENTRY_POINTS
      , classifiers          = [
          "Programming Language :: Python"
          , "Programming Language :: Python :: 2.7"
          , "Programming Language :: Python :: 3.5"
          , "Development Status :: 4 - Beta"
          , "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)"
          , ]
      , )
