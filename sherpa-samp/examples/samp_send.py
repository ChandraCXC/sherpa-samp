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

import sampy as samp
import numpy
import base64
import cStringIO
import traceback
import sys
import os

import time
import signal
import sherpa.astro.io as io

from sherpa_samp.utils import encode_string, decode_string, capture_exception
import sherpa_samp.sedexceptions as sedexceptions

_max  = numpy.finfo(numpy.float32).max
_tiny = numpy.finfo(numpy.float32).tiny
_eps  = numpy.finfo(numpy.float32).eps


MTYPE_SPECTRUM_FIT_SET_DATA = "spectrum.fit.set.data"
MTYPE_SPECTRUM_FIT_FIT = "spectrum.fit.fit"

MTYPE_SPECTRUM_FIT_CONFIDENCE = "spectrum.fit.confidence"
MTYPE_SPECTRUM_FIT_CONFIDENCE_EVENT = "spectrum.fit.confidence.event"
MTYPE_SPECTRUM_FIT_CONFIDENCE_STOP = "spectrum.fit.confidence.stop"

MTYPE_LOAD_TABLE_VOTABLE = "load.table.votable"
MTYPE_LOAD_TABLE_FITS = "load.table.fits"
MTYPE_SPECTRUM_FIT_SET_MODEL = "spectrum.fit.set.model" 
MTYPE_SPECTRUM_FIT_SET_STATISTIC = "spectrum.fit.set.statistic"
MTYPE_SPECTRUM_FIT_SET_METHOD = "spectrum.fit.set.method"     
MTYPE_SPECTRUM_FIT_SET_CONFIDENCE = "spectrum.fit.set.confidence"
MTYPE_SPECTRUM_FIT_CALC_STATISTIC_VALUE = "spectrum.fit.calc.statistic.value"
MTYPE_SPECTRUM_FIT_CALC_STATISTIC_VALUES = "spectrum.fit.calc.statistic.values" 
MTYPE_SPECTRUM_FIT_CALC_MODEL_VALUES = "spectrum.fit.calc.model.values"
MTYPE_SPECTRUM_FIT_CALC_FLUX_VALUE = "spectrum.fit.calc.flux.value"

metadata={
    "samp.name" : "Client",
    "samp.description.text" : "Test Client 1",
    "cli1.version" :"0.01",
    "samp.icon.url" : "http://hea-www.harvard.edu/~kjg/logo.png",
    "samp.description.html" : "http://cxc.harvard.edu/ciao",
    "samp.documentation.url" : "http://cxc.harvard.edu/ciao"
    }

cli = samp.SAMPIntegratedClient(metadata)
cli.connect()


pardict = {}

def call(mtype, params):
    clients = cli.getSubscribedClients(mtype)
    for recipient_id in clients:
        msg_id = cli.call(recipient_id, mtype,
                          {'samp.mtype'  : mtype,
                           'samp.params' : params})
        #print 'calling', recipient_id

def die():
    if cli.isConnected():
        cli.disconnect()
    sys.exit()


def _sig_handler(signum, frame):
    if cli.isConnected():
        cli.disconnect()
    raise KeyboardInterrupt()

signal.signal(signal.SIGINT, _sig_handler)


def save_pars(modcomps=[]):
    global pardict
    for comp in modcomps:
        for par in comp['pars']:
            pardict[par['name']] = par['val']

def update_pars(fitresults):
    global pardict
    for name, val in zip(fitresults['parnames'], fitresults['parvals']):
        if pardict.has_key(name):
            pardict[name] = val


def set_pars(modcomps=[]):
    global pardict
    for comp in modcomps:
        for par in comp['pars']:
            par['val'] = float(pardict.get(par['name']))



def get_data(filename):
    colkeys, cols, fname = io.backend.get_ascii_data(filename)
    data = {}
    data['name'] = fname
    data['x'] = encode_string(cols[0])
    data['y'] = encode_string(cols[1])
    if len(cols) > 2:
        data['staterror'] = encode_string(cols[2])
    return data


def get_model():
    name = "powlaw1d.p1+const1d.c1"
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
    c0 = { 'name' : 'c1.c0',
           'val'  : float(1.0),
           'min'  : float(-_max),
           'max'  : float(_max),
           'frozen' : bool(False),
           }
    c1 = { 'name' : 'const1d.c1',
           'pars' : [c0]
           }
    model = { 'name' : name,
              'parts' : [p1, c1] }

    if pardict:
        set_pars(model['parts'])
    else:
        save_pars(model['parts'])

    return model

def get_stat():
    return { 'name' : 'chi2xspecvar' }

def get_method():
    return { 'name' : 'moncar',

# LEVMAR

             # 'config' : { 'maxfev' : int(10000),
             #              'ftol'   : float(_eps),
             #              'epsfcn' : float(_eps),
             #              'gtol'   : float(_eps),
             #              'xtol'   : float(_eps),
             #              'factor' : float(100),
             #              }

# MONCAR

             'config' : { 'maxfev' : int(10000),
                          'ftol'   : float(_eps),
                          'population_size' : 'INDEF',
                          'seed'   : int(74815),
                          'weighting_factor'   : float(0.8),
                          'xprob' : float(0.9),
                          }

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



def spectrum_fit_set_data(filename):
    try:

        data = get_data(filename)
        params = {'datasets' : [data]}
        call(MTYPE_SPECTRUM_FIT_SET_DATA, params)

    except Exception, e:
        print str(e)
        raise e


def spectrum_fit_set_model():
    try:
        model = get_model()
        params = {'models' : [model]}
        call(MTYPE_SPECTRUM_FIT_SET_MODEL, params)

    except Exception, e:
        print str(e)
        raise e



def spectrum_fit_set_statistic():
    try:
        stat = get_stat()
        params = {'stat' : stat}
        call(MTYPE_SPECTRUM_FIT_SET_STATISTIC, params)

    except Exception, e:
        print str(e)
        raise e


def spectrum_fit_set_method():
    try:
        method = get_method()
        params = {'method' : method}
        call(MTYPE_SPECTRUM_FIT_SET_METHOD, params)

    except Exception, e:
        print str(e)
        raise e


def spectrum_fit_set_confidence():
    try:
        confidence = get_confidence()
        params = {'confidence' : confidence}
        call(MTYPE_SPECTRUM_FIT_SET_CONFIDENCE, params)

    except Exception, e:
        print str(e)
        raise e


def spectrum_fit_fit(filename):
    try:
        data = get_data(filename)
        model = get_model()
        stat = get_stat()
        method = get_method()
        
        params = {'datasets' : [data, data],
                  'models'   : [model, model],
                  'stat'     : stat,
                  'method'   : method,
                  }

        call(MTYPE_SPECTRUM_FIT_FIT, params)

    except Exception, e:
        print str(e)
        raise e


def spectrum_fit_confidence(filename):
    try:
        data = get_data(filename)
        model = get_model()
        stat = get_stat()
        method = get_method()
        confidence = get_confidence()
        params = {'datasets'   : [data],
                  'models'     : [model],
                  'stat'       : stat,
                  'method'     : method,
                  'confidence' : confidence,
                  }

        call(MTYPE_SPECTRUM_FIT_CONFIDENCE, params)

    except Exception, e:
        print str(e)
        raise e


def spectrum_fit_confidence_stop(mtype):
    try:
        call(mtype, {})
    except Exception, e:
        print str(e)
        raise e
    

def spectrum_fit_calc_statistic_value(filename):
    try:
        data = get_data(filename)
        model = get_model()
        stat = get_stat()
        method = get_method()

        params = {'datasets' : [data],
                  'models'   : [model],
                  'stat'     : stat,
                  }

        call(MTYPE_SPECTRUM_FIT_CALC_STATISTIC_VALUE, params)

    except Exception, e:
        print str(e)
        raise e


def spectrum_fit_calc_statistic_values(filename):
    try:
        data = get_data(filename)
        model = get_model()
        stat = get_stat()
        method = get_method()
        
        params = {'datasets' : [data],
                  'models'   : [model],
                  'stat'     : stat,
                  'params'   : [{'p1.gamma' : 2, 'p1.ampl' : 1, 'c1.c0' : 1},
                                {'p1.gamma' : 1, 'p1.ampl' : 2, 'c1.c0' : 1},
                                {'p1.gamma' : 1, 'p1.ampl' : 1, 'c1.c0' : 2}],
                  }

        call(MTYPE_SPECTRUM_FIT_CALC_STATISTIC_VALUES, params)

    except Exception, e:
        print str(e)
        raise e


def spectrum_fit_calc_model_values(filename):
    try:
        data = get_data(filename)
        model = get_model()
        stat = get_stat()
        method = get_method()
        
        params = {'datasets' : [data],
                  'models'   : [model],
                  }

        call(MTYPE_SPECTRUM_FIT_CALC_MODEL_VALUES, params)

    except Exception, e:
        print str(e)
        raise e



def spectrum_fit_calc_flux_value(filename):
    try:
        data = get_data(filename)
        model = get_model()
        stat = get_stat()
        method = get_method()
        
        params = {'datasets' : [data],
                  'models'   : [model],
                  'type'     : 'photon',
                  }

        call(MTYPE_SPECTRUM_FIT_CALC_FLUX_VALUE, params)

    except Exception, e:
        print str(e)
        raise e




def spectrum_fit_response(private_key, sender_id, msg_id, response):

    try:

        if response['samp.status'] == samp.SAMP_STATUS_OK:
            print "OK"

        else:
            exception = getattr(sedexceptions,
                                response['samp.result']['exception'], None)
            if exception is None:
                raise Exception('Unknown exception ' + 
                                response['samp.result']['exception'])
            else:
                #raise exception(response['samp.result']['message'])
                print exception(response['samp.result']['message'])
                die()

    except Exception, e:
        print str(e)
        raise e


def spectrum_fit_fit_receive_response(private_key, sender_id, msg_id, response):

    try:

        if response['samp.status'] == samp.SAMP_STATUS_OK:
            results =  response['samp.result']
            if not results:
                print 'no fit results!'
                return

            results['parvals'] = decode_string(results['parvals'])
            print results
            update_pars(results)
            #print pardict
        else:
            exception = getattr(sedexceptions,
                                response['samp.result']['exception'], None)
            if exception is None:
                raise Exception('Unknown exception ' +
                                response['samp.result']['exception'])
            else:
                #print exception, response['samp.result']['message']
                #raise exception(response['samp.result']['message'])
                print exception(response['samp.result']['message'])
                die()

    except Exception, e:
        print capture_exception()
        return


def spectrum_fit_confidence_receive_response(private_key, sender_id, msg_id,
                                             response):

    try:

        if response['samp.status'] == samp.SAMP_STATUS_OK:
            results =  response['samp.result']

            for key in ['parvals','parmins','parmaxes']:
                results[key] = decode_string(results[key])

            print results
            #update_pars(results)

        else:
            exception = getattr(sedexceptions,
                                response['samp.result']['exception'], None)
            if exception is None:
                raise Exception('Unknown exception ' +
                                response['samp.result']['exception'])
            else:
                #print exception, response['samp.result']['message']
                #raise exception(response['samp.result']['message'])
                print exception(response['samp.result']['message'])
                die()

    except Exception, e:
        print capture_exception()
        return


def spectrum_fit_calc_statistic_value_receive_response(private_key, sender_id,
                                                       msg_id, response):

    try:

        if response['samp.status'] == samp.SAMP_STATUS_OK:
            results =  response['samp.result']
            print results['results']
        else:
            exception = getattr(sedexceptions,
                                response['samp.result']['exception'], None)
            if exception is None:
                raise Exception('Unknown exception ' +
                                response['samp.result']['exception'])
            else:
                print exception(response['samp.result']['message'])
                die()

    except Exception, e:
        print capture_exception()
        return

def spectrum_fit_calc_statistic_values_receive_response(private_key, sender_id,
                                                        msg_id, response):

    try:

        if response['samp.status'] == samp.SAMP_STATUS_OK:
            results =  response['samp.result']
            print decode_string(results['results'])
        else:
            exception = getattr(sedexceptions,
                                response['samp.result']['exception'], None)
            if exception is None:
                raise Exception('Unknown exception ' +
                                response['samp.result']['exception'])
            else:
                print exception(response['samp.result']['message'])
                die()

    except Exception, e:
        print capture_exception()
        return


def spectrum_fit_calc_model_values_receive_response(private_key,
                                                    sender_id, msg_id, response):

    try:

        if response['samp.status'] == samp.SAMP_STATUS_OK:
            results =  response['samp.result']
            for ii in results['results']:
                print decode_string(ii)
        else:
            exception = getattr(sedexceptions, response['samp.result']['exception'], None)
            if exception is None:
                raise Exception('Unknown exception ' + response['samp.result']['exception'])
            else:
                print exception(response['samp.result']['message'])
                die()

    except Exception, e:
        print capture_exception()
        return

def receive_call(private_key, sender_id, msg_id, mtype, params, extra):
    #print params
    #print "receiving call now...", mtype, params, extra
    pass

cli.bindReceiveCall("samp.hub.*", receive_call)

def receive_notification(private_key, sender_id, mtype, params, extra):
    #print params
    #print "receiving notification now..."
    print params

#cli.bindReceiveNotification("samp.hub.*", receive_notification)

def receive_response(private_key, sender_id, msg_id, response):
    #print response
    #print "receiving response now...", response
    pass


cli.bindReceiveResponse(MTYPE_LOAD_TABLE_FITS, spectrum_fit_response)
cli.bindReceiveResponse(MTYPE_LOAD_TABLE_VOTABLE, spectrum_fit_response)
cli.bindReceiveResponse(MTYPE_SPECTRUM_FIT_SET_DATA, spectrum_fit_response)
cli.bindReceiveResponse(MTYPE_SPECTRUM_FIT_SET_MODEL, spectrum_fit_response)
cli.bindReceiveResponse(MTYPE_SPECTRUM_FIT_SET_STATISTIC, spectrum_fit_response)
cli.bindReceiveResponse(MTYPE_SPECTRUM_FIT_SET_METHOD, spectrum_fit_response)
cli.bindReceiveResponse(MTYPE_SPECTRUM_FIT_SET_CONFIDENCE, spectrum_fit_response)
cli.bindReceiveResponse(MTYPE_SPECTRUM_FIT_CONFIDENCE_STOP, spectrum_fit_response)

cli.bindReceiveResponse(MTYPE_SPECTRUM_FIT_CALC_STATISTIC_VALUE, spectrum_fit_calc_statistic_value_receive_response)
cli.bindReceiveResponse(MTYPE_SPECTRUM_FIT_CALC_STATISTIC_VALUES, spectrum_fit_calc_statistic_values_receive_response)
cli.bindReceiveResponse(MTYPE_SPECTRUM_FIT_CALC_MODEL_VALUES, spectrum_fit_calc_model_values_receive_response)
cli.bindReceiveResponse(MTYPE_SPECTRUM_FIT_CALC_FLUX_VALUE, spectrum_fit_calc_statistic_values_receive_response)

cli.bindReceiveResponse(MTYPE_SPECTRUM_FIT_FIT, spectrum_fit_fit_receive_response)
cli.bindReceiveResponse(MTYPE_SPECTRUM_FIT_CONFIDENCE, spectrum_fit_confidence_receive_response)
cli.bindReceiveResponse("samp.hub.*", receive_response)

cli.bindReceiveNotification(MTYPE_SPECTRUM_FIT_CONFIDENCE_EVENT, receive_notification)


if __name__ == '__main__':

    from optparse import OptionParser
    __parser = OptionParser( )
    __parser.add_option("--file", dest="file", default=None,
                        help="a PHA fits file")
    (__options, __args) = __parser.parse_args( )
    
    if __options.file is None:
        raise IOError("please supply a PHA file with '--file'")

    spectrum_fit_fit(__options.file)

    time.sleep(3.) # delay so client receives fitting parameters before conf().

    spectrum_fit_confidence(__options.file)

    spectrum_fit_set_data(__options.file)
    spectrum_fit_set_model()    
    spectrum_fit_set_statistic()
    spectrum_fit_set_method()
    spectrum_fit_set_confidence()
    spectrum_fit_calc_statistic_value(__options.file)
    spectrum_fit_calc_statistic_values(__options.file)
    spectrum_fit_calc_model_values(__options.file)
    spectrum_fit_calc_flux_value(__options.file)
