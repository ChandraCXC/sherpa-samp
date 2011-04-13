#!/usr/bin/env python 

import unittest
import sampy as samp
import numpy
import time
import base64
import thread

import sherpa_samp.mtypes
import sherpa.all
import sherpa.astro.all


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


def get_data():
    x = numpy.arange(0.1, 10.1, 0.1)
    y = numpy.array(
        [ 114, 47, 35, 30, 40, 27, 30, 26, 24, 20, 26, 35,
          29, 28, 34, 36, 43, 39, 33, 47, 44, 46, 53, 56,
          52, 53, 49, 57, 49, 36, 33, 42, 49, 45, 42, 32,
          31, 34, 18, 24, 25, 11, 17, 17, 11,  9,  8,  5,
           4, 10,  3,  4,  6,  3,  0,  2,  4,  4,  0,  1,
           2,  0,  3,  3,  0,  2,  1,  2,  3,  0,  1,  0,
           1,  0,  0,  1,  3,  3,  0,  2,  0,  0,  1,  2,
           0,  1,  0,  1,  1,  0,  1,  1,  1,  1,  1,  1,
           1,  0,  1,  0
          ]
        )
    err = numpy.ones(100)*0.4
    data = {}
    data['name'] = 'gaussian test'
    data['x'] = encode_string(x)
    data['y'] = encode_string(y)
    data['staterror'] = encode_string(err)
    return data


def get_model():
    name = "powlaw1d.p1+gauss1d.g1"
    gamma = { 'name'   : 'p1.gamma',
              'val'    : float(1.0),
              'min'    : float(-10),
              'max'    : float(10),
              'frozen' : bool(False),
              }
    ampl = { 'name' : 'p1.ampl',
             'val'  : float(1.0),
             'min'  : float(0.0),
             'max'  : float(_max),
             'frozen' : bool(False),
             }
    ref = { 'name' : 'p1.ref',
            'val'  : float(1.0),
            'min'  : float(-_max),
            'max'  : float(_max),
            'frozen' : bool(True),
            }
    p1 = { 'name' : 'powlaw1d.p1',
           'pars' : [gamma, ref, ampl]
           }

    fwhm = { 'name' : 'g1.fwhm',
           'val'  : float(1.0),
           'min'  : float(_tiny),
           'max'  : float(_max),
           'frozen' : bool(False),
           }
    pos = { 'name' : 'g1.pos',
            'val'  : float(1.0),
            'min'  : float(-_max),
            'max'  : float(_max),
            'frozen' : bool(False),
            }
    norm = { 'name' : 'g1.ampl',
             'val'  : float(1.0),
             'min'  : float(-_max),
             'max'  : float(_max),
             'frozen' : bool(False),
             }
    g1 = { 'name' : 'gauss1d.g1',
           'pars' : [fwhm, pos, norm]
           }
    model = { 'name' : name,
              'parts' : [p1, g1] }
    return model


def get_stat():
    return { 'name' : 'chi2gehrels' }


def get_method():
    return { 'name' : 'levmar',

# LEVMAR

             'config' : { 'maxfev' : int(10000),
                          'ftol'   : float(_eps),
                          'epsfcn' : float(_eps),
                          'gtol'   : float(_eps),
                          'xtol'   : float(_eps),
                          'factor' : float(100),
                          }

# MONCAR

             # 'config' : { 'maxfev' : int(10000),
             #              'ftol'   : float(_eps),
             #              'population_size' : 'INDEF',
             #              'seed'   : int(74815),
             #              'weighting_factor'   : float(0.8),
             #              'xprob' : float(0.9),
             #              }

             }


def get_confidence():
    return { 'name' : 'conf',
             'config' : { 'sigma'        : float(1.0),
                          'eps'          : float(0.01),
                          'maxiters'     : int(200),
                          'soft_limits'  : bool(False),
                          'fast'         : bool(True),
                          'max_rstat'    : int(100),
                          'maxfits'      : int(5),
                          'numcores'     : int(1),
                          'openinterval' : bool(False),
                          'remin'        : float(0.01),
                          'tol'          : float(0.2),
                          }
             }


MTYPE_SPECTRUM_FIT_FIT = "spectrum.fit.fit"

class MTypeTester(unittest.TestCase):

    _fit_results_bench = {'rstat': 89.29503933428586,
                          'qval': 0.0,
                          'succeeded': 1,
                          'numpoints': 100,
                          'dof': 95,
                          'nfev': 93,
                          'statval': 8483.0287367571564,
                          'parnames': ['p1.gamma', 'p1.ampl', 'g1.fwhm', 'g1.pos', 'g1.ampl'], 
                          'parvals': numpy.array([1.0701938169914813,
                                                  9.1826254677279469,
                                                  2.5862083052721028,
                                                  2.601619746022207,
                                                  47.262657692418749])
                          }

    def setUp(self):
        self.hub = samp.SAMPHubServer()
        self.hub.start()

        time.sleep(0.1)

        thread.start_new_thread(sherpa_samp.mtypes.main, ())
        self.cli = samp.SAMPIntegratedClient()
        self.cli.connect()

        time.sleep(0.1)


    def test_spectrum_fit_fit(self):

        data = get_data()
        model = get_model()
        stat = get_stat()
        method = get_method()
        params = {
            #'datasets' : [data, data],
            #'models'   : [model, model],
            'datasets' : [data],
            'models'   : [model],
            'stat'     : stat,
            'method'   : method,
            }
        response = self.cli.callAndWait(
            sherpa_samp.mtypes.cli.getPublicId(),
            {'samp.mtype'  : MTYPE_SPECTRUM_FIT_FIT,
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

    def tearDown(self):
        sherpa_samp.mtypes.stop()

        time.sleep(0.5)

        if self.cli is not None and self.cli.isConnected():
            self.cli.disconnect()

        time.sleep(0.1)

        self.hub.stop()


if __name__ == '__main__':
    unittest.main()