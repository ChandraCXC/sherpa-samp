#!/usr/bin/env python
#
#  Copyright (C) 2011  Smithsonian Astrophysical Observatory
#
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

import setuptools
from numpy.distutils.core import setup

setup(name='sherpa_samp',
      version='2.1',
      author='Smithsonian Astrophysical Observatory / Chandra X-Ray Center',
      author_email='cxchelp@head.cfa.harvard.edu',
      url='http://cxc.harvard.edu/sherpa/',
      description='A SAMP interface to the Sherpa modeling and fitting package for scientific data analysis',
      packages=['sherpa_samp', 'sherpa_samp.sedstacker_iris'],
      test_suite="tests",
      package_data={'sherpa_samp': ['tests/*'],
                    'sherpa_samp.sedstacker_iris':['tests/*']},
      entry_points = {
         'console_scripts' : ['sherpa-samp=sherpa_samp.mtypes:main'],
      },
      requires = ['astLib', 'scipy', 'sherpa', 'numpy'],
      )
