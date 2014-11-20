import base64
import unittest
import os
import os.path
import sampy as samp
import time
import thread
import sherpa_samp
from sedstacker.iris.sed import IrisStack, IrisSed
import numpy


_max  = numpy.finfo(numpy.float32).max
_tiny = numpy.finfo(numpy.float32).tiny
_eps  = numpy.finfo(numpy.float32).eps


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

    x = numpy.array([1,5,10,15,50,100])
    y = numpy.array([1,5,10,15,50,100]) * 0.1
    yerr = numpy.array([1,5,10,15,50,100]) * 0.01

def test_normalize(self):

        #data = get_data()
        #model = get_model()
        #stat = get_stat()
        #method = get_method()
        params = {
            'x' : [data],
            'y'   : [model],
            'yerr'     : stat,
            'method'   : method,
            }
        response = self.cli.callAndWait(
            sherpa_samp.mtypes.cli.getPublicId(),
            {'samp.mtype'  : MTYPE_STACK_NORMALIZE,
             'samp.params' : params},
            "10")

        assert response['samp.status'] == 'samp.ok'

        results = response['samp.result']
        results['parvals'] = decode_string(results['parvals'])

        for key in ["succeeded", "numpoints", "nfev"]:
            assert self._fit_results_bench[key] == int(results[key])

        for key in ["rstat", "qval", "statval", "dof"]:
            assert numpy.allclose(float(self._fit_results_bench[key]), float(results[key]),
                                  1.e-7, 1.e-7)

        for key in ["parvals"]:
            assert numpy.allclose(self._fit_results_bench[key], results[key],
                                  1.e-7, 1.e-7)

        self._test_tablemodel()
        self._test_usermodel()

    def test_normalize_by_int_avg_mult(self):

        sed1 = IrisSed(x=self.x,y=self.y,yerr=self.yerr)
        sed2 = IrisSed(x=numpy.array([2,4,5,8,10]), y=numpy.arange(5)+1.0, yerr=numpy.arange(5)+1.0*0.1)
        y = numpy.array([5.0, 15.0, 7.0, 4.5, 13.5, 10.5])
        x = numpy.array([0.5, 1.5, 3.0, 5.0, 10.5, 21.0])
        sed3 = IrisSed(x=x, y=y, yerr=y*0.1)

        stack = IrisStack([sed1, sed2, sed3])

        # normalize SEDs with avg statistic
        norm_stack = stack.normalize_by_int(minWavelength='min', maxWavelength='max',
                         stats='avg', y0=1.0, norm_operator=0,
                         correct_flux=False, z0=None)

        numpy.testing.assert_array_almost_equal(norm_stack[0].y, 0.49234923*sed1.y)
        numpy.testing.assert_array_almost_equal(norm_stack[1].y, 9.846*sed2.y)
        self.assertAlmostEqual(norm_stack[2].norm_constant, 1.1529274)


    def test_normalize_by_int_median_mult(self):

        sed1 = IrisSed(x=self.x,y=self.y,yerr=self.yerr)
        sed2 = IrisSed(x=numpy.array([2,4,5,8,10]), y=numpy.arange(5)+1.0, yerr=numpy.arange(5)+1.0*0.1)
        y = numpy.array([5.0, 15.0, 7.0, 4.5, 13.5, 10.5])
        x = numpy.array([0.5, 1.5, 3.0, 5.0, 10.5, 21.0])
        sed3 = IrisSed(x=x, y=y, yerr=y*0.1)

        stack = IrisStack([sed1, sed2, sed3])

        # normalize SEDs with avg statistic
        norm_stack = stack.normalize_by_int(stats='median')

        numpy.testing.assert_array_almost_equal(norm_stack[0].y, 0.4270427*sed1.y)
        numpy.testing.assert_array_almost_equal(norm_stack[1].y, 8.54*sed2.y)
        self.assertAlmostEqual(norm_stack[2].norm_constant, 1.0)


    def test_normalize_by_int_avg_add(self):

        sed1 = IrisSed(x=self.x,y=self.y,yerr=self.yerr)
        sed2 = IrisSed(x=numpy.array([2,4,5,8,10]), y=numpy.arange(5)+1.0, yerr=numpy.arange(5)+1.0*0.1)
        y = numpy.array([5.0, 15.0, 7.0, 4.5, 13.5, 10.5])
        x = numpy.array([0.5, 1.5, 3.0, 5.0, 10.5, 21.0])
        sed3 = IrisSed(x=x, y=y, yerr=y*0.1)

        stack = IrisStack([sed1, sed2, sed3])

        # normalize SEDs with avg statistic
        norm_stack = stack.normalize_by_int(stats='avg', norm_operator=1)

        numpy.testing.assert_array_almost_equal(norm_stack[0].y, 0 - 253.8 + sed1.y)
        numpy.testing.assert_array_almost_equal(norm_stack[1].y, 221.15 + sed2.y)
        self.assertAlmostEqual(norm_stack[2].norm_constant, 32.65)


    def test_normalize_at_point_avg_mult(self):

        sed1 = IrisSed(x=self.x,y=self.y,yerr=self.yerr)
        sed2 = IrisSed(x=numpy.array([2,4,5,8,10]), y=numpy.arange(5)+1.0, yerr=numpy.arange(5)+1.0*0.1)
        y = numpy.array([5.0, 15.0, 7.0, 4.5, 13.5, 10.5])
        x = numpy.array([0.5, 1.5, 3.0, 5.5, 10.5, 21.0])
        sed3 = IrisSed(x=x, y=y, yerr=y*0.1)

        stack = IrisStack([sed1, sed2, sed3])

        # normalize SEDs with avg statistic
        norm_stack = stack.normalize_at_point(5.0, 1.0, stats='avg', norm_operator=0)

        numpy.testing.assert_array_almost_equal(norm_stack[0].y, (8/3.)/0.5*sed1.y)
        numpy.testing.assert_array_almost_equal(norm_stack[1].y, (8/3.)/3.0*sed2.y)
        self.assertAlmostEqual(norm_stack[2].norm_constant, (8/3.)/4.5)


    def setUp(self):
        #path = os.getcwd()
        #lockfilename = os.path.join(path,"samp")
        #self.hub = samp.SAMPHubServer(lockfile=lockfilename)
        self.hub = samp.SAMPHubServer()
        self.hub.start()

        time.sleep(5)

        thread.start_new_thread(sherpa_samp.mtypes.main, ())
        self.cli = samp.SAMPIntegratedClient()
        self.cli.connect()

        time.sleep(5)


   def tearDown(self):
        sherpa_samp.mtypes.stop()

        time.sleep(1)

        if self.cli is not None and self.cli.isConnected():
            self.cli.disconnect()

        time.sleep(1)

        self.hub.stop()


if __name__ == '__main__':
    unittest.main()