#!/usr/bin/env python

from setuptools import setup

__version__ = '0.1'

setup(
  name = 'kraller',
  version = __version__,
  description = 'A little application to allow signups with keys for accounts on a server',
  author = 'Brian Stack',
  author_email = 'bis12@case.edu',
  url = 'http://github.com/hacsoc/kraller',
  long_description=open("README").read(),
  install_requires = [
    'flask',
  ],
  license = 'BSD',
  classifiers = [
    'Development Status :: 2 - Pre-Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Programming Language :: Python',
    'Operating System :: OS Independent',
    'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
  ]
)
