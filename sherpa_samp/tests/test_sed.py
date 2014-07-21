#  Copyright (C) 2013  Smithsonian Astrophysical Observatory
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

import unittest

from sherpa_samp.utils import DictionaryClass
from sherpa_samp.sed import Sed

class  Sed_TestCase(unittest.TestCase):
    #def setUp(self):
    #    self.foo = Sed_()
    #

    #def tearDown(self):
    #    self.foo.dispose()
    #    self.foo = None

    def test_sed(self):
        s = Sed(range(10), range(10))
        
        self.assertEqual(tuple(range(10)), tuple(s.wavelength))
        self.assertEqual(tuple(range(10)), tuple(s.flux))
        
        s = Sed(range(10), range(10), 3)
        
        self.assertEqual(tuple(range(10)), tuple(s.wavelength))
        self.assertEqual(tuple(range(10)), tuple(s.flux))
        
    def test_dictionary_class(self):
        obj = DictionaryClass({'foo' : 'bar', 'nested' : {'myvar' : 5}})
        
        self.assertEqual('bar', obj.foo)
        self.assertEqual(5, obj.nested.myvar)
        
        self.assertEqual({'foo' : 'bar', 'nested' : {'myvar' : 5}}, obj.get_dict())
        
    def test_convert(self):
        obj = DictionaryClass({"from-redshift":5})
        
        self.assertEqual(5, obj.from_redshift)
        
    def test_redshift(self):
        pass


if __name__ == '__main__':
    unittest.main()

