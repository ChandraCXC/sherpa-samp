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
from math import sqrt
import numpy
import time
import sampy as samp
import thread
import sys
from sherpa_samp import mtypes


def decode_string(encoded_string, dtype="<f8"):
    decoded_string = base64.b64decode(encoded_string)
    array = numpy.fromstring(decoded_string, dtype=numpy.float64)
    return array.byteswap()


def encode_string(array, dtype="<f8"):
    array = numpy.asarray(array, dtype=numpy.float64).byteswap()
    decoded_string = array.tostring()
    encoded_string = base64.b64encode(decoded_string)
    return encoded_string


MTYPE_STACK_STACK = "stack.stack"


class TestStack(unittest.TestCase):

    x = numpy.linspace(1000,10000, num=1000)
    y = numpy.linspace(1000,10000, num=1000)*1e-10
    yerr = 0.1*y
    z = 0.5

    def test_stack_wavg(self):

        seg1 = {'x': encode_string(self.x), 'y': encode_string(self.y), 'yerr': encode_string(self.yerr), 'z': str(self.z)}
        seg2 = {'x': encode_string(self.x), 'y': encode_string(self.y), 'yerr': encode_string(self.yerr), 'z': str(self.z)}
        seg3 = {'x': encode_string(self.x), 'y': encode_string(self.y), 'yerr': encode_string(self.yerr), 'z': str(self.z)}
        seg4 = {'x': encode_string(self.x), 'y': encode_string(self.y), 'yerr': encode_string(self.yerr), 'z': str(self.z)}
        seg5 = {'x': encode_string(self.x), 'y': encode_string(self.y), 'yerr': encode_string(self.yerr), 'z': str(self.z)}
        seg6 = {'x': encode_string(self.x), 'y': encode_string(self.y), 'yerr': encode_string(self.yerr), 'z': str(self.z)}

        params = {}

        params['segments'] = [seg1, seg2, seg3, seg4, seg5, seg6]
        params['binsize'] = str(self.x[1] - self.x[0])
        params['statistic'] = 'wavg'
        params['smooth-binsize'] = '5'
        params['log-bin'] = 'false'
        params['smooth'] = 'false'

        start = time.clock()
        response = self.cli.callAndWait(
            mtypes.cli.getPublicId(),
            {'samp.mtype': MTYPE_STACK_STACK,
             'samp.params': params},
            "50")
        end = time.clock()
        print 'Time to run SAMP function: ', str(end-start)
        #assert response['samp.status'] == 'samp.ok'

        stacked_seds = response['samp.result']['segments']

        self.assertEqual(decode_string(stacked_seds[0]['yerr'])[3], sqrt((self.yerr[3]**2)*6))
        numpy.testing.assert_array_almost_equal(decode_string(stacked_seds[0]['y']), self.y, decimal=6)
        self.assertEqual(decode_string(stacked_seds[0]['counts'])[0], 6)
        self.assertEqual(len(stacked_seds), 1)

    def test_stack_wavg_40(self):

        segments = []
        for i in range(40):
            seg = {'x': encode_string(self.x), 'y': encode_string(self.y), 'yerr': encode_string(self.yerr), 'z': str(self.z)}
            segments.append(seg)

        params = {}

        params['segments'] = segments
        params['binsize'] = str(self.x[1] - self.x[0])
        params['statistic'] = 'wavg'
        params['smooth-binsize'] = '5'
        params['log-bin'] = 'false'
        params['smooth'] = 'false'

        start = time.clock()
        response = self.cli.callAndWait(
            mtypes.cli.getPublicId(),
            {'samp.mtype': MTYPE_STACK_STACK,
             'samp.params': params},
            "10")
        end = time.clock()
        print 'Time to run SAMP function: ', str(end-start)

        assert response['samp.status'] == 'samp.ok'

        stacked_seds = response['samp.result']['segments']

        self.assertEqual(decode_string(stacked_seds[0]['yerr'])[3], sqrt((self.yerr[3]**2)*40))
        numpy.testing.assert_array_almost_equal(decode_string(stacked_seds[0]['y']), self.y, decimal=6)
        self.assertEqual(decode_string(stacked_seds[0]['counts'])[0], 40)

        # def test_stack_user_defined_func(self):
    #
    #     seg1 = {'x': encode_string(self.x), 'y': encode_string(self.y), 'yerr': encode_string(self.yerr), 'z': str(self.z)}
    #     seg2 = {'x': encode_string(self.x), 'y': encode_string(self.y), 'yerr': encode_string(self.yerr), 'z': str(self.z)}
    #     seg3 = {'x': encode_string(self.x), 'y': encode_string(self.y), 'yerr': encode_string(self.yerr), 'z': str(self.z)}
    #     seg4 = {'x': encode_string(self.x), 'y': encode_string(self.y), 'yerr': encode_string(self.yerr), 'z': str(self.z)}
    #     seg5 = {'x': encode_string(self.x), 'y': encode_string(self.y), 'yerr': encode_string(self.yerr), 'z': str(self.z)}
    #     seg6 = {'x': encode_string(self.x), 'y': encode_string(self.y), 'yerr': encode_string(self.yerr), 'z': str(self.z)}
    #
    #     params = {}
    #
    #     params['segments'] = [seg1, seg2, seg3, seg4, seg5, seg6]
    #     params['binsize'] = str(self.x[1] - self.x[0])
    #     params['statistic'] = 'my_wavg'
    #     params['smooth-binsize'] = '5'
    #     params['log-bin'] = 'false'
    #     params['smooth'] = 'false'
    #
    #     start = time.clock()
    #     response = self.cli.callAndWait(
    #         mtypes.cli.getPublicId(),
    #         {'samp.mtype': MTYPE_STACK_STACK,
    #          'samp.params': params},
    #         "10")
    #     end = time.clock()
    #     print 'Time to run SAMP function: ', str(end-start)
    #
    #     assert response['samp.status'] == 'samp.ok'
    #
    #     stacked_seds = response['samp.result']['segments']
    #
    #     self.assertEqual(decode_string(stacked_seds[0]['yerr'])[3], sqrt((self.yerr[3]**2)*6))
    #     numpy.testing.assert_array_almost_equal(decode_string(stacked_seds[0]['y']), self.y, decimal=6)
    #     self.assertEqual(decode_string(stacked_seds[0]['counts'])[0], 6)
    #     self.assertEqual(len(stacked_seds), 1)


    @classmethod
    def setUpClass(cls):
        cls.hub = samp.SAMPHubServer()
        cls.hub.start()

        time.sleep(5)

        thread.start_new_thread(mtypes.main, ())
        cls.cli = samp.SAMPIntegratedClient()
        cls.cli.connect()

        time.sleep(5)

    @classmethod
    def tearDownClass(cls):
        mtypes.stop()

        time.sleep(1)

        if cls.cli is not None and cls.cli.isConnected():
            cls.cli.disconnect()

        time.sleep(1)

        cls.hub.stop()


if __name__ == '__main__':
    unittest.main()