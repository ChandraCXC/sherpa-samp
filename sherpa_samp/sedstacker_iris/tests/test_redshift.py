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

import base64
import unittest
import time
import thread
import sys
from sherpa_samp.utils import DictionaryClass
from sherpa_samp import mtypes
import sampy as samp
import numpy
import logging


_max = numpy.finfo(numpy.float32).max
_tiny = numpy.finfo(numpy.float32).tiny
_eps = numpy.finfo(numpy.float32).eps

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)


def decode_string(encoded_string, dtype="<f8"):
    decoded_string = base64.b64decode(encoded_string)
    array = numpy.fromstring(decoded_string, dtype=numpy.float64)
    return array.byteswap()


def encode_string(array, dtype="<f8"):
    array = numpy.asarray(array, dtype=numpy.float64).byteswap()
    decoded_string = array.tostring()
    encoded_string = base64.b64encode(decoded_string)
    return encoded_string


MTYPE_STACK_REDSHIFT = "stack.redshift"


class TestRedshift(unittest.TestCase):

    # @classmethod
    # def setUpClass(cls):
    #     cls.hub = samp.SAMPHubServer()
    #     cls.hub.start()
    #
    #     time.sleep(5)
    #
    #     thread.start_new_thread(mtypes.main, ())
    #     cls.cli = samp.SAMPIntegratedClient()
    #     cls.cli.connect()
    #
    #     time.sleep(5)

    def setUp(self):
        self.hub = samp.SAMPHubServer()
        self.hub.start()

        time.sleep(5)

        thread.start_new_thread(mtypes.main, ())
        self.cli = samp.SAMPIntegratedClient()
        self.cli.connect()

        time.sleep(5)

    def test_redshift_no_correct_flux(self):

        length1 = numpy.arange(1000,10000,10).size
        x1 = encode_string(numpy.arange(1000,10000,10))
        y1 = encode_string(numpy.arange(1000,10000,10))
        yerr1 = numpy.empty(length1)
        yerr1[:] = numpy.nan
        yerr1 = encode_string(yerr1)
        z1 = str(1.0)

        length2 = numpy.arange(1000,10000,500).size
        x2 = encode_string(numpy.arange(1000,10000,500))
        y2 = encode_string(numpy.arange(1000,10000,500))
        yerr2 = numpy.empty(length2)
        yerr2[:] = numpy.nan
        yerr2 = encode_string(yerr2)
        z2 = str(0.5)

        x3 = encode_string(numpy.arange(1000,10000,500))
        y3 = encode_string(numpy.arange(1000,10000,500))
        yerr3 = numpy.empty(length2)
        yerr3[:] = numpy.nan
        yerr3 = encode_string(yerr3)
        z3 = str(0.35)

        params = {}

        segment1 = {'x': x1, 'y': y1, 'yerr': yerr1, 'z': z1}
        segment2 = {'x': x2, 'y': y2, 'yerr': yerr2, 'z': z2}
        segment3 = {'x': x3, 'y': y3, 'yerr': yerr3, 'z': z3}

        params['segments'] = [segment1, segment2, segment3]
        params['z0'] = '0.4'
        params['correct_flux'] = 'false'

        response = self.cli.callAndWait(
            mtypes.cli.getPublicId(),
            {'samp.mtype': MTYPE_STACK_REDSHIFT,
             'samp.params': params},
            "10")

        assert response['samp.status'] == 'samp.ok'

        results = response['samp.result']

        shifted_stack = DictionaryClass(results).get_dict()['segments']

        self.assertNotEqual(float(shifted_stack[0]['z']), float(shifted_stack[1]['z']))
        self.assertEqual(float(shifted_stack[0]['z']), 1.0)
        self.assertAlmostEqual(float(decode_string(shifted_stack[0]['x'])[10]), 770.0)
        numpy.testing.assert_array_almost_equal(decode_string(shifted_stack[0]['y']), decode_string(y1))

    def test_redshift_correct_flux(self):

        x1 = encode_string(numpy.array([3823.0, 4470.9, 5657.1, 6356.3, 7000.0]))
        y1 = encode_string(numpy.array([1.3e-11, 2.56e-11, 7.89e-11, 6.5e-11, 1.2e-10]))
        yerr1 = encode_string(numpy.array([1.0e-13, 1.0e-13, 1.0e-13, 1.0e-13, 1e-12]))
        z1 = str(1.65)
        id1 = "sed1"
        segment1 = {'x': x1, 'y': y1, 'yerr': yerr1, 'z': z1, 'id': id1}

        x2 = encode_string(numpy.linspace(3000.0, 10000.0, num=10000))
        y2 = encode_string(numpy.linspace(1e-13, 1e-11, num=10000))
        yerr2 = numpy.empty(10000)
        yerr2[:] = numpy.nan
        yerr2 = encode_string(yerr2)
        z2 = str(1.65)
        id2 = "sed2"
        segment2 = {'x': x2, 'y': y2, 'yerr': yerr2, 'z': z2, 'id': id2}

        params = {}

        params['segments'] = [segment1, segment2]

        params['correct_flux'] = 'true'
        params['z0'] = '0.1'

        response = self.cli.callAndWait(
            mtypes.cli.getPublicId(),
            {'samp.mtype': MTYPE_STACK_REDSHIFT,
             'samp.params': params},
            "10")

        assert response['samp.status'] == 'samp.ok'

        results = response['samp.result']

        shifted_stack = DictionaryClass(results).get_dict()['segments']

        self.assertEqual(len(shifted_stack), 2)

        #y values
        # segment1
        spec_z0 = decode_string(x1)*(1+0.1)/(1+float(z1))
        zflux = numpy.trapz(decode_string(y1), decode_string(x1))
        z0flux = numpy.trapz(decode_string(y1), spec_z0)
        const = zflux/z0flux

        numpy.testing.assert_array_almost_equal(decode_string(shifted_stack[0]['y']), decode_string(y1)*const)
        numpy.testing.assert_array_almost_equal(decode_string(shifted_stack[0]['yerr']), decode_string(yerr1)*const)
        numpy.testing.assert_array_almost_equal(decode_string(shifted_stack[0]['x']), spec_z0)

        # segment2
        spec_z0 = decode_string(x2)*(1+0.1)/(1+float(z2))
        zflux = numpy.trapz(decode_string(y2), decode_string(x2))
        z0flux = numpy.trapz(decode_string(y2), spec_z0)
        const = zflux/z0flux

        numpy.testing.assert_array_almost_equal(decode_string(shifted_stack[1]['y']), decode_string(y2)*const)
        numpy.testing.assert_array_almost_equal(decode_string(shifted_stack[1]['x']), spec_z0)


    def test_redshift_no_z(self):

        length1 = numpy.arange(1000,10000,10).size
        x1 = encode_string(numpy.arange(1000,10000,10))
        y1 = encode_string(numpy.arange(1000,10000,10))
        yerr1 = numpy.empty(length1)
        yerr1[:] = numpy.nan
        yerr1 = encode_string(yerr1)
        z1 = str(1.0)
        id1 = "sed1"

        length2 = numpy.arange(1000,10000,500).size
        x2 = encode_string(numpy.arange(1000,10000,500))
        y2 = encode_string(numpy.arange(1000,10000,500))
        yerr2 = numpy.empty(length2)
        yerr2[:] = numpy.nan
        yerr2 = encode_string(yerr2)
        z2 = str(numpy.nan)
        id2 = "sed2"

        x3 = encode_string(numpy.arange(1000,10000,500))
        y3 = encode_string(numpy.arange(1000,10000,500))
        yerr3 = numpy.empty(length2)
        yerr3[:] = numpy.nan
        yerr3 = encode_string(yerr3)
        z3 = str(0.35)
        id3 = "sed3"

        params = {}

        segment1 = {'x': x1, 'y': y1, 'yerr': yerr1, 'z': z1, 'id': id1}
        segment2 = {'x': x2, 'y': y2, 'yerr': yerr2, 'z': z2, 'id': id2}
        segment3 = {'x': x3, 'y': y3, 'yerr': yerr3, 'z': z3, 'id': id3}

        params['segments'] = [segment1, segment2, segment3]
        params['z0'] = '0.5'
        params['correct_flux'] = 'false'

        response = self.cli.callAndWait(
            mtypes.cli.getPublicId(),
            {'samp.mtype': MTYPE_STACK_REDSHIFT,
             'samp.params': params},
            "10")

        assert response['samp.status'] == 'samp.ok'

        results = response['samp.result']

        shifted_stack = DictionaryClass(results).get_dict()['segments']

        self.assertEqual(len(shifted_stack), 3)
        self.assertAlmostEqual(float(decode_string(shifted_stack[0]['x'])[1]), 757.5)
        self.assertAlmostEqual(float(decode_string(shifted_stack[1]['x'])[1]), 1500.0)
        self.assertAlmostEqual(float(decode_string(shifted_stack[2]['x'])[1]), 1666.6666667)

    # @classmethod
    # def tearDownClass(cls):
    #     mtypes.stop()
    #
    #     time.sleep(1)
    #
    #     if cls.cli is not None and cls.cli.isConnected():
    #         cls.cli.disconnect()
    #
    #     time.sleep(1)
    #
    #     cls.hub.stop()
    def tearDown(self):
        mtypes.stop()

        time.sleep(1)

        if self.cli is not None and self.cli.isConnected():
            self.cli.disconnect()

        time.sleep(1)

        self.hub.stop()


if __name__ == '__main__':
    unittest.main()