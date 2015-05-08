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
import numpy as np

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
        s = Sed(range(10), range(10), range(10))
        
        self.assertEqual(tuple(range(10)), tuple(s.wavelength))
        self.assertEqual(tuple(range(10)), tuple(s.flux))
        
        s = Sed(range(10), range(10), range(10), 3)
        
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

        # this test should make sure that the yerr's are sorted with
        # their corresponding (x, y) points

        # what the yerrs should be
        yerr = np.array(np.arange(14))+1

        # make dummy data. I'm using duplicate values in the x array
        # because duplicate x values are common in Iris SEDs.
        y = np.array([0.68, 0.30, 0.35, 0.30, 0.22, 0.25, 0.63, 0.51, 0.14, 0.14, 0.14, 0.14, 0.14, 1.22])
        x = y

        s = Sed(x, y, yerr, z=1)
        s.redshift(0)

        np.testing.assert_array_equal(s.err, [9, 10, 11, 12, 13, 5, 6, 2, 4, 3, 8, 7, 1, 14])

        yerr = np.array(np.arange(30))+1
        y = np.array(np.arange(30))+1
        x = np.array(np.arange(10))+1
        x = np.concatenate([x, x, x], axis=0)

        s = Sed(x, y, yerr, z=1)
        s.redshift(0)

        # since y and yerr are the same before redshifting, and only y is affected during redshifting,
        # will can multiply the resultant SED flux array by a constant to get back to the flux error array.
        # In this case, the constant is 0.5.
        np.testing.assert_array_equal(s.err, s.flux * 0.5)


if __name__ == '__main__':
    unittest.main()

