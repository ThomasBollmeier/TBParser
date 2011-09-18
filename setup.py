# coding=UTF-8

from distutils.core import setup
import tbparser

setup(
      name = tbparser.PACKAGE,
      version = tbparser.PACKAGE_VERSION,
      description = 'A simple parser',
      author = 'Thomas Bollmeier',
      author_email = 'tbollmeier@web.de',
      license = 'GPLv3',
      packages = ['tbparser']
      )
