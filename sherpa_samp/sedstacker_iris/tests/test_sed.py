import base64
import unittest
import time
import thread
from sherpa_samp.utils import DictionaryClass
from sherpa_samp import mtypes
import sampy as samp
from sedstacker.iris.sed import IrisStack, IrisSed
import numpy


_max = numpy.finfo(numpy.float32).max
_tiny = numpy.finfo(numpy.float32).tiny
_eps = numpy.finfo(numpy.float32).eps


def decode_string(encoded_string, dtype="<f8"):
    decoded_string = base64.b64decode(encoded_string)
    array = numpy.fromstring(decoded_string, dtype=numpy.float64)
    return array.byteswap()


def encode_string(array, dtype="<f8"):
    array = numpy.asarray(array, dtype=numpy.float64).byteswap()
    decoded_string = array.tostring()
    encoded_string = base64.b64encode(decoded_string)
    return encoded_string


MTYPE_STACK_NORMALIZE = "stack.normalize"


class TestIrisSedStacker(unittest.TestCase):

    def test_normalize_by_int_avg_mult(self):
        x1 = encode_string(numpy.array([1, 5, 10, 15, 50, 100]))
        y1 = encode_string(numpy.array([1, 5, 10, 15, 50, 100]) * 0.1)
        yerr1 = encode_string(numpy.array([1, 5, 10, 15, 50, 100]) * 0.01)

        x2 = encode_string(numpy.array([2, 4, 5, 8, 10]))
        y2 = encode_string(numpy.arange(5) + 1.0)
        yerr2 = encode_string(numpy.arange(5) + 1.0 * 0.1)

        y3 = numpy.array([5.0, 15.0, 7.0, 4.5, 13.5, 10.5])
        yerr3 = encode_string(y3 * 0.1)
        y3 = encode_string(y3)
        x3 = encode_string(numpy.array([0.5, 1.5, 3.0, 5.0, 10.5, 21.0]))

        params = {}

        segment1 = {'x': x1, 'y': y1, 'yerr': yerr1}
        segment2 = {'x': x2, 'y': y2, 'yerr': yerr2}
        segment3 = {'x': x3, 'y': y3, 'yerr': yerr3}

        params['segments'] = [segment1, segment2, segment3]

        params['norm_operator'] = '0'
        params['y0'] = '1.0'
        params['xmin'] = 'min'
        params['xmax'] = 'max'
        params['stats'] = 'avg'
        params['integrate'] = 'true'

        response = self.cli.callAndWait(
            mtypes.cli.getPublicId(),
            {'samp.mtype': MTYPE_STACK_NORMALIZE,
             'samp.params': params},
            "10")

        assert response['samp.status'] == 'samp.ok'

        results = response['samp.result']

        norm_stack = DictionaryClass(results)

        numpy.testing.assert_array_almost_equal(decode_string(norm_stack.segments[0].y), 0.49234923 * decode_string(y1))
        numpy.testing.assert_array_almost_equal(decode_string(norm_stack.segments[1].y), 9.846 * decode_string(y2))
        self.assertAlmostEqual(float(norm_stack.segments[2].norm_constant), 1.1529274)

    def test_normalize_by_int_median_mult(self):
        x1 = encode_string(numpy.array([1, 5, 10, 15, 50, 100]))
        y1 = encode_string(numpy.array([1, 5, 10, 15, 50, 100]) * 0.1)
        yerr1 = encode_string(numpy.array([1, 5, 10, 15, 50, 100]) * 0.01)

        x2 = encode_string(numpy.array([2, 4, 5, 8, 10]))
        y2 = encode_string(numpy.arange(5) + 1.0)
        yerr2 = encode_string(numpy.arange(5) + 1.0 * 0.1)

        y3 = numpy.array([5.0, 15.0, 7.0, 4.5, 13.5, 10.5])
        yerr3 = encode_string(y3 * 0.1)
        y3 = encode_string(y3)
        x3 = encode_string(numpy.array([0.5, 1.5, 3.0, 5.0, 10.5, 21.0]))

        params = {}

        segment1 = {'x': x1, 'y': y1, 'yerr': yerr1}
        segment2 = {'x': x2, 'y': y2, 'yerr': yerr2}
        segment3 = {'x': x3, 'y': y3, 'yerr': yerr3}

        params['segments'] = [segment1, segment2, segment3]

        params['norm_operator'] = '0';
        params['y0'] = '1.0'
        params['xmin'] = 'min'
        params['xmax'] = 'max'
        params['stats'] = 'median'
        params['integrate'] = 'true'

        response = self.cli.callAndWait(
            mtypes.cli.getPublicId(),
            {'samp.mtype': MTYPE_STACK_NORMALIZE,
             'samp.params': params},
            "10")

        assert response['samp.status'] == 'samp.ok'

        results = response['samp.result']

        norm_stack = DictionaryClass(results)

        numpy.testing.assert_array_almost_equal(decode_string(norm_stack.segments[0].y), 0.4270427 * decode_string(y1))
        numpy.testing.assert_array_almost_equal(decode_string(norm_stack.segments[1].y), 8.54 * decode_string(y2))
        self.assertAlmostEqual(float(norm_stack.segments[2].norm_constant), 1.0)

    def test_normalize_by_int_avg_add(self):
        x1 = encode_string(numpy.array([1, 5, 10, 15, 50, 100]))
        y1 = encode_string(numpy.array([1, 5, 10, 15, 50, 100]) * 0.1)
        yerr1 = encode_string(numpy.array([1, 5, 10, 15, 50, 100]) * 0.01)

        x2 = encode_string(numpy.array([2, 4, 5, 8, 10]))
        y2 = encode_string(numpy.arange(5) + 1.0)
        yerr2 = encode_string(numpy.arange(5) + 1.0 * 0.1)

        y3 = numpy.array([5.0, 15.0, 7.0, 4.5, 13.5, 10.5])
        yerr3 = encode_string(y3 * 0.1)
        y3 = encode_string(y3)
        x3 = encode_string(numpy.array([0.5, 1.5, 3.0, 5.0, 10.5, 21.0]))

        params = {}

        segment1 = {'x': x1, 'y': y1, 'yerr': yerr1}
        segment2 = {'x': x2, 'y': y2, 'yerr': yerr2}
        segment3 = {'x': x3, 'y': y3, 'yerr': yerr3}

        params['segments'] = [segment1, segment2, segment3]

        params['norm_operator'] = '1';
        params['y0'] = '1.0'
        params['xmin'] = 'min'
        params['xmax'] = 'max'
        params['stats'] = 'avg'
        params['integrate'] = 'true'

        response = self.cli.callAndWait(
            mtypes.cli.getPublicId(),
            {'samp.mtype': MTYPE_STACK_NORMALIZE,
             'samp.params': params},
            "10")

        assert response['samp.status'] == 'samp.ok'

        results = response['samp.result']

        norm_stack = DictionaryClass(results)
        numpy.testing.assert_array_almost_equal(decode_string(norm_stack.segments[0].y), 0 - 253.8 + decode_string(y1))
        numpy.testing.assert_array_almost_equal(decode_string(norm_stack.segments[1].y), 221.15 + decode_string(y2))
        self.assertAlmostEqual(float(norm_stack.segments[2].norm_constant), 32.65)

    def test_normalize_at_point_avg_mult(self):

        x1 = encode_string(numpy.array([1, 5, 10, 15, 50, 100]))
        y1 = encode_string(numpy.array([1, 5, 10, 15, 50, 100]) * 0.1)
        yerr1 = encode_string(numpy.array([1, 5, 10, 15, 50, 100]) * 0.01)

        x2 = encode_string(numpy.array([2, 4, 5, 8, 10]))
        y2 = encode_string(numpy.arange(5) + 1.0)
        yerr2 = encode_string(numpy.arange(5) + 1.0 * 0.1)

        y3 = numpy.array([5.0, 15.0, 7.0, 4.5, 13.5, 10.5])
        yerr3 = encode_string(y3 * 0.1)
        y3 = encode_string(y3)
        x3 = encode_string(numpy.array([0.5, 1.5, 3.0, 5.5, 10.5, 21.0]))

        params = {}

        segment1 = {'x': x1, 'y': y1, 'yerr': yerr1}
        segment2 = {'x': x2, 'y': y2, 'yerr': yerr2}
        segment3 = {'x': x3, 'y': y3, 'yerr': yerr3}

        params['segments'] = [segment1, segment2, segment3]

        params['norm_operator'] = '0';
        params['y0'] = '1.0'
        params['x0'] = '5.0'
        params['stats'] = 'avg'
        params['integrate'] = 'false'

        response = self.cli.callAndWait(
            mtypes.cli.getPublicId(),
            {'samp.mtype': MTYPE_STACK_NORMALIZE,
             'samp.params': params},
            "10")

        assert response['samp.status'] == 'samp.ok'

        results = response['samp.result']

        norm_stack = DictionaryClass(results)

        numpy.testing.assert_array_almost_equal(decode_string(norm_stack.segments[0].y), (8/3.)/0.5*decode_string(y1))
        numpy.testing.assert_array_almost_equal(decode_string(norm_stack.segments[1].y), (8/3.)/3.0*decode_string(y2))
        self.assertAlmostEqual(float(norm_stack.segments[2].norm_constant), (8/3.)/4.5)

    def setUp(self):
        self.hub = samp.SAMPHubServer()
        self.hub.start()

        time.sleep(5)

        thread.start_new_thread(mtypes.main, ())
        self.cli = samp.SAMPIntegratedClient()
        self.cli.connect()

        time.sleep(5)

    def tearDown(self):
        mtypes.stop()

        time.sleep(1)

        if self.cli is not None and self.cli.isConnected():
            self.cli.disconnect()

        time.sleep(1)

        self.hub.stop()


if __name__ == '__main__':
    unittest.main()