#!/usr/bin/env python
#
#  Copyright (C) 2011, 2015  Smithsonian Astrophysical Observatory
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
from httplib import CannotSendRequest, ResponseNotReady

import sys
import time
import numpy
import signal
import multiprocessing

import sampy as samp

import sherpa_samp.sedexceptions as sedexceptions
import numpy as np
from sherpa_samp.session import SherpaSession, check_for_nans
from sherpa_samp.utils import encode_string, decode_string, capture_exception, DictionaryClass
# from sherpa_samp.sed import Sed
from astLib.astSED import Passband
from sherpa.utils import linear_interp, neville, nearest_interp
from sherpa_samp.interpolation import interp1d
from sherpa_samp.sedstacker_iris.sed import normalize, redshift, stack
from sedstacker.iris.sed import IrisSed, IrisStack
from sherpa_samp.sed import Sed
import sedstacker.sed

#
## Logging
#

import logging

from sherpa_samp.log import logfile

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                   format='[SHERPA] %(levelname)-8s %(asctime)s %(message)s',
                   datefmt='%a, %d %b %Y %H:%M:%S',
                   filename=logfile, # FIXME: user permissions!
                   filemode='a')

info = logger.info
warn = logger.warning
error = logger.error

metadata = {
    "samp.name" : "Sherpa",
    "samp.description.text" : "Sherpa SAMP Interface",
    "cli1.version" :"0.3.1",
    "samp.description.html" : "http://cxc.harvard.edu/sherpa",
    "samp.documentation.url" : "http://cxc.harvard.edu/sherpa"
    }

cli = samp.SAMPIntegratedClient(metadata, addr='localhost')


_fitting_tasks = []
_confidence_tasks = []


def _sig_handler(signum, frame):
    info("Got termination signal")
    if cli is not None:
        try:
            cli.disconnect()
        except Exception as e:
            warn("Could not disconnect cleanly")
            logging.exception(e)
    if signum == signal.SIGINT:
        info("Signal is SIGINT")
        raise KeyboardInterrupt()
    else:
        info("Signal is not SIGINT")
        sys.exit(1)

try:
    # Handle either keyboard interrupt from interactive
    # session, or termination signal
    signal.signal(signal.SIGINT, _sig_handler)   # I.e., kill -2
    signal.signal(signal.SIGTERM, _sig_handler)  # I.e., kill or kill -15
except ValueError:
    error("Cannot register signal handlers")
    sys.exit(1)


def reply_success(msg_id, mtype, params={}):
    for i in range(0, 100):
        try:
            cli.reply(msg_id, {"samp.status": samp.SAMP_STATUS_OK,
                   "samp.result": params,
                   })
            info("sent reply_success to " + msg_id)
        except (CannotSendRequest, ResponseNotReady) as e:
            warn("cannot send request:")
            logging.exception(e)
            continue
        break

def reply_error(msg_id, exception, e, mtype):

    errtrace = capture_exception()
    logger.exception(e)
    #error(errtrace)
    cli.reply(msg_id, {"samp.status": samp.SAMP_STATUS_ERROR,
    #cli.reply(msg_id, {"samp.status": "samp.notok",
                       "samp.result": {"exception": str(exception.__name__),
                                       "message": str(e) #str(errtrace)
                                       },
                       "samp.error" : {"samp.errortxt" : "Sherpa exception"},
                       })
    info("sent reply_error to " + msg_id)
    #cli.disconnect()
    #sys.exit(1)


def notify(mtype, msg):
    cli.enotifyAll(mtype, message = msg)

    #cli.notify


class MtypeReceiveReplyNoResponse(object):

    def __init__(self, func, exceptionClass):
        self.func = func
        self.exceptionClass = exceptionClass

    def __call__(self, private_key, sender_id, msg_id, mtype, params, extra):

        try:
            info(self.func.__name__ + "()")

            try:

                self.func(private_key, sender_id, msg_id, mtype, params, extra)

            except Exception, e:
                reply_error(msg_id, exceptionClass, e, mtype)
                return

            reply_success(msg_id, mtype)

        except Exception:
            error(str(capture_exception()))



def load_table_votable(private_key, sender_id, msg_id, mtype, params, extra):
    """
    load_table_votable

    
    """
    try:
        info("load_table_votable()")

        try:

            pass

        except Exception, e:
            reply_error(msg_id, sedexceptions.DataException, e, mtype)
            return

        reply_success(msg_id, mtype)

    except Exception:
        error(str(capture_exception()))


def load_table_fits(private_key, sender_id, msg_id, mtype, params, extra):
    """
    load_table_fits

    
    """
    try:
        info("load_table_fits()")
        ui = SherpaSession()

        try:
            # native Sherpa command
            ui.session.load_table(params["url"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.DataException, e, mtype)
            return

        reply_success(msg_id, mtype)

    except Exception:
        error(str(capture_exception()))



def spectrum_fit_set_data(private_key, sender_id, msg_id, mtype, params, extra):
    """
    spectrum_fit_set_model

    
    """
    try:
        info("spectrum_fit_set_data()")
        ui = SherpaSession()

        try:
            ui.set_data(params["datasets"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.DataException, e, mtype)
            return

        reply_success(msg_id, mtype)

    except Exception:
        error(str(capture_exception()))




def spectrum_fit_set_model(private_key, sender_id, msg_id, mtype, params,
                           extra):
    """
    spectrum_fit_set_model

    
    """
    try:
        info("spectrum_fit_set_model()")
        ui = SherpaSession()

        try:
            usermodels = []
            if (params.has_key("usermodels")):
                usermodels = params["usermodels"]
            ui.set_parameters(params["models"], usermodels)

        except Exception, e:
            reply_error(msg_id, sedexceptions.ParameterException, e, mtype)
            return

        try:
            ui.set_model(params["models"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.ModelException, e, mtype)
            return

        reply_success(msg_id, mtype)

    except Exception:
        error(str(capture_exception()))



def spectrum_fit_set_statistic(private_key, sender_id, msg_id, mtype, params,
                               extra):
    """
    spectrum_fit_set_statistic

    
    """
    try:
        info("spectrum_fit_set_statistic()")
        ui = SherpaSession()

        try:
            ui.set_stat(params["stat"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.StatisticException, e, mtype)
            return

        reply_success(msg_id, mtype)

    except Exception:
        error(str(capture_exception()))



def spectrum_fit_set_method(private_key, sender_id, msg_id, mtype, params,
                            extra):
    """
    spectrum_fit_set_method

    
    """
    try:
        info("spectrum_fit_set_method()")
        ui = SherpaSession()

        try:
            ui.set_method(params["method"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.MethodException, e, mtype)
            return

        reply_success(msg_id, mtype)

    except Exception:
        error(str(capture_exception()))



def spectrum_fit_set_confidence(private_key, sender_id, msg_id, mtype, params,
                                extra):
    """
    spectrum_fit_set_confidence

    
    """
    try:
        info("spectrum_fit_set_confidence()")
        ui = SherpaSession()

        try:
            ui.set_confidence(params["confidence"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.ConfidenceException, e, mtype)
            return

        reply_success(msg_id, mtype)

    except Exception:
        error(str(capture_exception()))





def fit_worker(func, outq, errq):
    try:
        results = func()
        outq.put(results)

    except Exception:
        e = capture_exception()
        errq.put(e)
        outq.put(None)


def conf_worker(func, outq, errq):
    try:

        #confoutput = logging.StreamHandler()
        # confoutput = ConfStreamHandler(sys.stderr)
        # confoutput.setLevel(logging.INFO)
        # logger.addHandler(confoutput)

        results = func()
        outq.put(results)

    except Exception:
        e = capture_exception()
        errq.put(e)
        outq.put(None)


def spectrum_fit_fit(private_key, sender_id, msg_id, mtype, params, extra):
    """
    spectrum_fit_fit


    """
    try:
        info("spectrum_fit_fit()")
        ui = SherpaSession()

        info("ui session _sources: " + str(ui.session._sources))
        info("ui session _models: " + str(ui.session._models))
        info("ui session _model_components: " + str(ui.session._model_components))
        info("ui session _data: " + str(ui.session._data))

        try:
            ui.set_method(params["method"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.MethodException, e, mtype)
            return

        try:
            ui.set_data(params["datasets"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.DataException, e, mtype)
            return

        try:
            usermodels = []
            if (params.has_key("usermodels")):
                usermodels = params["usermodels"]
            ui.set_parameters(params["models"], usermodels)

        except Exception, e:
            reply_error(msg_id, sedexceptions.ParameterException, e, mtype)
            return

        try:
            ui.set_model(params["models"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.ModelException, e, mtype)
            return

        try:
            ui.set_stat(params["stat"])

            check_for_nans(ui)

        except Exception, e:
            reply_error(msg_id, sedexceptions.StatisticException, e, mtype)
            return

        results = None

        try:

            # native Sherpa command
            # tt = time.time()
            # ui.session.fit()
            # print 'fit in', (time.time() - tt)
            # results = ui.get_fit_results()

            outq = multiprocessing.Queue()
            errq = multiprocessing.Queue()

            def worker(ui_p):
                try:
                    signal.signal(signal.SIGTERM, signal.SIG_DFL)
                    ui_p.session.fit()
                    results = ui_p.get_fit_results()
                    outq.put(results)
                except Exception, e:
                    trace = capture_exception()
                    msg = str(trace)
                    if e.args:
                        msg = e.args[0]
                    errq.put( (msg, trace) )
                    outq.put(None)

            fit_task = multiprocessing.Process(target=worker, args=(ui,))

            global _fitting_tasks
            _fitting_tasks.append((fit_task, msg_id, mtype))

            tt = time.time()
            fit_task.start()
            #print 'fit PID', os.getpid()
            fit_task.join()
            print 'fit in', (time.time() - tt)

            #_fitting_tasks.remove((fit_task, msg_id, mtype))
            try:
                _fitting_tasks.pop(-1)
            except IndexError:
                pass

            if not errq.empty():
                msg, traceback = errq.get()
                error(traceback)
                raise Exception(msg)

            results = outq.get()

            # ids, fitobj = sherpa._session._get_fit(None)
            # fit_task = multiprocessing.Process(target=fit_worker,
            #                                    args=(fitobj.fit, outq, errq))

            # # FIXME: this needs to be thread safe!
            # _fitting_tasks.append(fit_task)

            # tt = time.time()
            # fit_task.start()
            # #print 'fit PID: ', os.getpid() 
            # pid = os.getpid()
            # fit_task.join()
            # print 'fit', pid, 'in', (time.time()-tt), 'secs'

            # _fitting_tasks.remove(fit_task)

            # if not errq.empty():
            #     raise Exception(errq.get())

            # results = get_fit_results(outq.get())

        except Exception, e:
            reply_error(msg_id, sedexceptions.FitException, e, mtype)
            return

        #thread = threading.Thread(target = run_fit)
        #results = thread.start()

        if results:
            try:
                reply_success(msg_id, mtype, results)
                return
            except Exception:
                error(str(capture_exception()))
                return

        reply_success(msg_id, mtype)

    except Exception:
        error(str(capture_exception()))



class ConfidenceHandler(logging.StreamHandler):
    def emit(self, record):
        message = record.getMessage()
        if record.name == 'sherpa' and record.levelname == 'INFO':
            notify(MTYPE_SPECTRUM_FIT_CONFIDENCE_EVENT, str(message))


def spectrum_fit_confidence(private_key, sender_id, msg_id, mtype, params,
                            extra):
    """
    spectrum_fit_confidence



    """
    try:
        info("spectrum_fit_confidence()")
        ui = SherpaSession()

        try:
            ui.set_method(params["method"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.MethodException, e, mtype)
            return

        try:
            ui.set_data(params["datasets"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.DataException, e, mtype)
            return

        try:
            usermodels = []
            if (params.has_key("usermodels")):
                usermodels = params["usermodels"]
            ui.set_parameters(params["models"], usermodels)

        except Exception, e:
            reply_error(msg_id, sedexceptions.ParameterException, e, mtype)
            return

        try:
            ui.set_model(params["models"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.ModelException, e, mtype)
            return

        try:
            ui.set_stat(params["stat"])

            check_for_nans(ui)

        except Exception, e:
            reply_error(msg_id, sedexceptions.StatisticException, e, mtype)
            return

        results = None

        try:

            #ui.set_confidence(params["confidence"])

            #handler = ConfidenceHandler()
            #handler.setLevel(logging.INFO)
            #logger = logging.getLogger('sherpa')
            #logger.setLevel(logging.INFO)
            #logger.addHandler(handler)

            #ui.run_confidence(params["confidence"])

            #logger.removeHandler(handler)

            #results = ui.get_confidence_results(params["confidence"])

            #
            ##  Multiprocessing 
            #

            outq = multiprocessing.Queue()
            errq = multiprocessing.Queue()

            def worker(ui_p, cdict):
                try:
                    signal.signal(signal.SIGTERM, signal.SIG_DFL)
                    ui_p.set_confidence(cdict)

                    handler = ConfidenceHandler()
                    handler.setLevel(logging.INFO)
                    logger = logging.getLogger('sherpa')
                    logger.setLevel(logging.INFO)
                    logger.addHandler(handler)

                    ui_p.run_confidence(cdict)

                    logger.removeHandler(handler)

                    results = ui_p.get_confidence_results(cdict)
                    outq.put(results)
                except Exception, e:
                    trace = capture_exception()
                    msg = str(trace)
                    if e.args:
                        msg = e.args[0]
                    errq.put( (msg, trace) )
                    outq.put(None)

            #methodobj = get_confidence(params["confidence"])
            #ids, fitobj = sherpa._session._get_fit(None, estmethod=methodobj)
            #conf_task = multiprocessing.Process(target=conf_worker,
            #                             args=(fitobj.est_errors, outq, errq))

            conf_task = multiprocessing.Process(target=worker,
                                                args=(ui, params["confidence"]))

            global _confidence_tasks
            # FIXME: this needs to be thread safe!
            _confidence_tasks.append((conf_task, msg_id, mtype))

            tt = time.time()
            conf_task.start()
            #print 'confidence PID', os.getpid()
            conf_task.join()
            print 'confidence in', (time.time() - tt)

            #_confidence_tasks.remove((conf_task, msg_id, mtype))
            try:
                _confidence_tasks.pop(-1)
            except IndexError:
                pass

            if not errq.empty():
                msg, traceback = errq.get()
                error(traceback)
                raise Exception(msg)

            #results = get_confidence_results(params["confidence"], outq.get())
            results = outq.get()

        except Exception, e:
            reply_error(msg_id, sedexceptions.FitException, e, mtype)
            return

        reply_success(msg_id, mtype, results)
    except Exception:
        error(str(capture_exception()))


def spectrum_fit_fit_stop(private_key, sender_id, msg_id, mtype, params, extra):
    """
    spectrum_fit_fit_stop


    """
    try:
        die = (lambda tasks : [task.terminate() for task in tasks
                               if task.exitcode is None])
        global _fitting_tasks
        if _fitting_tasks:
            for task_pkg in _fitting_tasks:
                task, fit_msg_id, fit_mtype = task_pkg
                reply_error(fit_msg_id, sedexceptions.FitException,
                            Exception("Fitting stopped"), fit_mtype)
                die([task])
            _fitting_tasks = []

    except Exception, e:
        reply_error(msg_id, sedexceptions.FitException, e, mtype)
        return

    try:
        reply_success(msg_id, mtype)
    except Exception:
        error(str(capture_exception()))
        return


def spectrum_fit_confidence_stop(private_key, sender_id, msg_id, mtype, params,
                                 extra):
    """
    spectrum_fit_confidence_stop


    """
    try:
        die = (lambda tasks : [task.terminate() for task in tasks
                               if task.exitcode is None])

        global _confidence_tasks
        if _confidence_tasks:
            for task_pkg in _confidence_tasks:
                task, conf_msg_id, conf_mtype = task_pkg
                reply_error(conf_msg_id, sedexceptions.ConfidenceException,
                            Exception("Confidence stopped"), conf_mtype)
                die([task])
            _confidence_tasks = []

    except Exception, e:
        reply_error(msg_id, sedexceptions.ConfidenceException, e, mtype)
        return

    try:
        reply_success(msg_id, mtype)
    except Exception:
        error(str(capture_exception()))
        return




def spectrum_fit_calc_statistic_value(private_key, sender_id, msg_id, mtype, params,
                                      extra):
    """
    spectrum_fit_calc_statistic_value



    """
    try:
        info("spectrum_fit_calc_statistic_value()")
        ui = SherpaSession()

        try:
            ui.set_data(params["datasets"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.DataException, e, mtype)
            return

        try:
            usermodels = []
            if (params.has_key("usermodels")):
                usermodels = params["usermodels"]
            ui.set_parameters(params["models"], usermodels)

        except Exception, e:
            reply_error(msg_id, sedexceptions.ParameterException, e, mtype)
            return

        try:
            ui.set_model(params["models"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.ModelException, e, mtype)
            return

        try:
            ui.set_stat(params["stat"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.StatisticException, e, mtype)
            return

        statval = None
        try:
            # native Sherpa command
            statval = ui.session.calc_stat()

        except Exception, e:
            reply_error(msg_id, sedexceptions.StatisticException, e, mtype)
            return

        reply_success(msg_id, mtype, { 'results' : statval})

    except Exception:
        error(str(capture_exception()))



def spectrum_fit_calc_statistic_values(private_key, sender_id, msg_id, mtype,
                                       params, extra):
    """
    spectrum_fit_calc_statistic_values



    """
    try:
        info("spectrum_fit_calc_statistic_values()")
        ui = SherpaSession()

        try:
            ui.set_data(params["datasets"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.DataException, e, mtype)
            return

        try:
            usermodels = []
            if (params.has_key("usermodels")):
                usermodels = params["usermodels"]
            ui.set_parameters(params["models"], usermodels)

        except Exception, e:
            reply_error(msg_id, sedexceptions.ParameterException, e, mtype)
            return

        try:
            ui.set_model(params["models"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.ModelException, e, mtype)
            return

        try:
            ui.set_stat(params["stat"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.StatisticException, e, mtype)
            return

        statvals = []
        try:
            for pardict in params["params"]:
                for parkey in pardict.keys():

                    # native Sherpa command
                    ui.session.set_par(parkey, pardict[parkey])

                # native Sherpa command
                statvals.append(ui.session.calc_stat())
            statvals = encode_string(statvals)

        except Exception, e:
            reply_error(msg_id, sedexceptions.StatisticException, e, mtype)
            return

        reply_success(msg_id, mtype, {'results' : statvals})

    except Exception:
        error(str(capture_exception()))



def spectrum_fit_calc_model_values(private_key, sender_id, msg_id, mtype,
                                   params, extra):
    """
    spectrum_fit_calc_model_values



    """
    try:
        info("spectrum_fit_calc_model_values()")
        ui = SherpaSession()

        try:
            ui.set_data(params["datasets"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.DataException, e, mtype)
            return

        try:
            usermodels = []
            if (params.has_key("usermodels")):
                usermodels = params["usermodels"]
            ui.set_parameters(params["models"], usermodels)

        except Exception, e:
            reply_error(msg_id, sedexceptions.ParameterException, e, mtype)
            return

        try:
            ui.set_model(params["models"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.ModelException, e, mtype)
            return

        modelvals = {}
        try:
            # native Sherpa commands
            data  = ui.session.get_data(0)
            model = ui.session.get_model(0)

            vals = data.eval_model(model)
            vals = encode_string(vals)

            modelvals["y"] = vals
            modelvals["x"] = encode_string(ui.session.get_data(0).x)
            modelvals["staterror"] = encode_string(numpy.ones_like(ui.session.get_data(0).x))

        except Exception, e:
            reply_error(msg_id, sedexceptions.ModelException, e, mtype)
            return

        reply_success(msg_id, mtype, modelvals)

    except Exception:
        error(str(capture_exception()))



def spectrum_fit_calc_flux_value(private_key, sender_id, msg_id, mtype, params,
                                      extra):
    """
    spectrum_fit_calc_flux_value



    """
    try:
        info("spectrum_fit_calc_flux_value()")
        ui = SherpaSession()

        try:
            ui.set_data(params["datasets"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.DataException, e, mtype)
            return

        try:
            usermodels = []
            if (params.has_key("usermodels")):
                usermodels = params["usermodels"]
            ui.set_parameters(params["models"], usermodels)

        except Exception, e:
            reply_error(msg_id, sedexceptions.ParameterException, e, mtype)
            return

        try:
            ui.set_model(params["models"])

        except Exception, e:
            reply_error(msg_id, sedexceptions.ModelException, e, mtype)
            return


        fluxvals = []
        try:

            # native Sherpa command
            for id in ui.session.list_data_ids():
                fluxfunc = ui.get_flux(params["type"])
                fluxvals.append(fluxfunc(id=id))

            fluxvals = encode_string(fluxvals)

        except Exception, e:
            reply_error(msg_id, sedexceptions.ModelException, e, mtype)
            return

        reply_success(msg_id, mtype, { 'results' : fluxvals})

    except Exception:
        error(str(capture_exception()))


def spectrum_redshift_calc(private_key, sender_id, msg_id, mtype, params,
                                      extra):
    """
    spectrum_redshift_calc



    """
    try:
        info("spectrum_redshift_calc()")
        try:
            payload = DictionaryClass(params)
            x = decode_string(payload.x)
            y = decode_string(payload.y)
            yerr = decode_string(payload.yerr)
            from_redshift = float(payload.from_redshift)
            to_redshift = float(payload.to_redshift)

            sed = Sed(x, y, yerr, from_redshift)
            sed.redshift(to_redshift)

            payload.x = encode_string(sed.wavelength)
            payload.y = encode_string(sed.flux)
            payload.yerr = encode_string(sed.err)

            reply_success(msg_id, mtype, payload)

        except Exception, e:
            reply_error(msg_id, sedexceptions.SEDException, e, mtype)
            return

    except Exception:
        error(str(capture_exception()))

def spectrum_integrate(private_key, sender_id, msg_id, mtype, params,
                                      extra):
    """
    spectrum_integrate



    """
    try:
        info("spectrum_integrate()")
        try:
            payload = DictionaryClass(params)

            x = decode_string(payload.x)
            y = decode_string(payload.y)

            sed = Sed(x, y)

            response = dict()
            response['points'] = list()

            for curve in payload.curves:
                pb = Passband(curve.file_name)
                flux = sed.calcFlux(pb)
                point = dict()
                point['id'] = curve.id
                point['wavelength'] = curve.eff_wave
                point['flux'] = str(flux)
                response['points'].append(point)

            for window in payload.windows:
                xmin = float(window.min)
                xmax = float(window.max)
                flux = sed.integrate(xmin, xmax)
                point = dict()
                point['id'] = window.id
                point['wavelength'] = str((xmax+xmin)/2)
                point['flux'] = str(flux)
                response['points'].append(point)

            reply_success(msg_id, mtype, response)

        except Exception, e:
            reply_error(msg_id, sedexceptions.SEDException, e, mtype)
            return

    except Exception:
        error(str(capture_exception()))

def spectrum_interpolate(private_key, sender_id, msg_id, mtype, params,
                                      extra):
    """
    spectrum_interpolate



    """

    try:
        info("spectrum_interpolate()")
        try:
            methods = {'Neville' : neville,
                       'Linear' : linear_interp,
                       'Nearest Neighbor' : nearest_interp,
                       'Linear Spline' : interp1d,
                       }
            payload = DictionaryClass(params)
            x = decode_string(payload.x)
            y = decode_string(payload.y)
            x_min = max(float(payload.x_min), min(x))
            x_max = min(float(payload.x_max), max(x))
            method = methods[payload.method]
            info("method " + method.__name__)
            n_bins = int(payload.n_bins)

            log = payload.log=='true';

            sed = Sed(x, y)
            newSed = sed.interpolate(method, (x_min, x_max), n_bins, log);

            filtered = False

            if payload.smooth == "true":
                info('smoothing')
                newSed = filter(newSed)
                newSed.smooth(int(payload.box_size))

            if payload.normalize=="true":
                info('normalizing')
                if not filtered:
                    newSed = filter(newSed)
                newSed.normalise()

            payload.x = encode_string(newSed.wavelength)
            payload.y = encode_string(newSed.flux)

            reply_success(msg_id, mtype, payload)
            info("success")

        except Exception, e:
            reply_error(msg_id, sedexceptions.SEDException, e, mtype)
            error("error: " + repr(e))
            return

    except Exception:
        error(str(capture_exception()))

def filter(sed):
    x = sed.wavelength
    y = sed.flux
    c = numpy.array((x,y)).T
    c = c[~np.isnan(c).any(1)].T
    x = c[0]
    y = c[1]
    return Sed(x,y)

def stack_redshift(private_key, sender_id, msg_id, mtype, params,
                                      extra):
    try:
        info("stack_redshift()")
        try:
            payload = DictionaryClass(params)
            seds = []
            for segment in payload.segments:
                x = decode_string(segment.x)
                y = decode_string(segment.y)
                yerr = decode_string(segment.yerr)
                z = float(segment.z)
                id_ = str(segment.id)
                seds.append(IrisSed(x=x, y=y, yerr=yerr, z=z, id=id_))
            z0 = float(payload.z0)
            correct_flux = payload.correct_flux == "true"

            result = redshift(IrisStack(seds), z0, correct_flux)

            for i, segment in enumerate(payload.segments):
                segment.x = encode_string(result[i].x)
                segment.y = encode_string(result[i].y)
                segment.yerr = encode_string(result[i].yerr)

            payload.excludeds = result.excluded

            reply_success(msg_id, mtype, payload.get_dict())

        except Exception, e:
            reply_error(msg_id, sedexceptions.SEDException, e, mtype)
            return

    except Exception:
        error(str(capture_exception()))

def stack_normalize(private_key, sender_id, msg_id, mtype, params,
                                      extra):
    try:
        info("stack_normalize()")
        try:
            payload = DictionaryClass(params)
            seds = []
            for segment in payload.segments:
                x = decode_string(segment.x)
                y = decode_string(segment.y)
                yerr = decode_string(segment.yerr)
                id_ = str(segment.id)
                seds.append(IrisSed(x=x, y=y, yerr=yerr, id=id_))
            stack = IrisStack(seds)

            result = normalize(stack, payload)
            for i, segment in enumerate(payload.segments):
                segment.x = encode_string(result[i].x)
                segment.y = encode_string(result[i].y)
                segment.yerr = encode_string(result[i].yerr)
                segment.norm_constant = str(result[i].norm_constant)
            payload.excludeds = result.excluded
            reply_success(msg_id, mtype, payload.get_dict())

        except Exception, e:
            reply_error(msg_id, sedexceptions.SEDException, e, mtype)
            return

    except Exception:
        error(str(capture_exception()))

def stack_stack(private_key, sender_id, msg_id, mtype, params,
                                      extra):
    try:
        info("stack_stack()")
        try:
            payload = DictionaryClass(params)
            seds = []
            for segment in payload.segments:
                x = decode_string(segment.x)
                y = decode_string(segment.y)
                yerr = decode_string(segment.yerr)
                seds.append(IrisSed(x=x, y=y, yerr=yerr))
            i_stack = IrisStack(seds)

            binsize = float(payload.binsize)
            statistic = str(payload.statistic)
            smooth = payload.smooth == "true"
            smooth_binsize = float(payload.smooth_binsize)
            logbin = payload.log_bin == "true"

            result = sedstacker.sed.stack(i_stack, binsize, statistic, fill='remove', smooth=smooth, smooth_binsize=smooth_binsize, logbin=logbin)

            payload.segments[0].x = encode_string(result.x)
            payload.segments[0].y = encode_string(result.y)
            payload.segments[0].yerr = encode_string(result.yerr)
            payload.segments[0].counts = encode_string(result.counts)
            payload.segments = [payload.segments[0]]
            get_dict = payload.get_dict()
            reply_success(msg_id, mtype, payload.get_dict())

        except Exception, e:
            reply_error(msg_id, sedexceptions.SEDException, e, mtype)
            return

    except Exception:
        error(str(capture_exception()))


def ping(private_key, sender_id, msg_id, mtype, params, extra):
    reply_success(msg_id, mtype, {})

#
## SAMP MTypes
#


_mtypes = {
    "load.table.votable"          : load_table_votable,
    "load.table.fits"             : load_table_fits,
    "spectrum.fit.set.data"       : spectrum_fit_set_data,
    "spectrum.fit.set.model"      : spectrum_fit_set_model,
    "spectrum.fit.set.statistic"  : spectrum_fit_set_statistic,
    "spectrum.fit.set.method"     : spectrum_fit_set_method,
    "spectrum.fit.set.confidence" : spectrum_fit_set_confidence,
    "spectrum.fit.fit"            : spectrum_fit_fit,
    "spectrum.fit.fit.stop"       : spectrum_fit_fit_stop,
    "spectrum.fit.confidence"     : spectrum_fit_confidence,
    "spectrum.fit.confidence.stop": spectrum_fit_confidence_stop,
    "spectrum.fit.calc.statistic.value"  : spectrum_fit_calc_statistic_value,
    "spectrum.fit.calc.statistic.values" : spectrum_fit_calc_statistic_values,
    "spectrum.fit.calc.model.values"     : spectrum_fit_calc_model_values,
    "spectrum.fit.calc.flux.value"       : spectrum_fit_calc_flux_value,
    "spectrum.redshift.calc"      : spectrum_redshift_calc,
    "spectrum.interpolate"   : spectrum_interpolate,
    "spectrum.integrate"   : spectrum_integrate,
    "stack.redshift" : stack_redshift,
    "stack.normalize" : stack_normalize,
    "stack.stack" : stack_stack,
    "sherpa.ping" : ping,
}

MTYPE_SPECTRUM_FIT_CONFIDENCE_EVENT = "spectrum.fit.confidence.event"


__serving = True

def stop():
    global __serving
    __serving = False
    _sig_handler(signal.SIGINT, None)


def register():
    #
    ##  Register SAMP MTypes
    #

    for mtype in _mtypes:
        cli.bindReceiveCall(mtype, _mtypes[mtype])

    def receive_call(private_key, sender_id, msg_id, mtype, params, extra):
        #print "receive_call()..."
        pass

    cli.bindReceiveCall("samp.hub.*", receive_call)

    def receive_notification(private_key, sender_id, mtype, params, extra):
        #print params
        #print "receiving notification now..."
        pass

    cli.bindReceiveNotification("samp.hub.*", receive_notification)


    def receive_response(private_key, sender_id, msg_id, response):
        #print response
        #print "receiving response now..."
        pass

    cli.bindReceiveResponse("samp.hub.*", receive_response)



def main():
    info("Starting " + __name__)
    global cli
    cli = samp.SAMPIntegratedClient(metadata, addr='localhost')
    try:
        global __serving
        last_ping = time.time()
        while __serving:
            try:
                time.sleep(1.5)
                if cli.hub.getRunningHubs() and cli.isConnected():
                    if not connected:
                        info("Successful ping at: "+str(last_ping))
                    connected = True
                    last_ping = time.time()
                else:
                    connected = False
                if not connected:
                    info("not connected")
                    try:
                        info("trying connection")
                        cli.connect()
                        info("trying registration")
                        register()
                        info("registered")
                    except samp.SAMPHubError as e:
                        warn("got SAMPHubError")
                        logging.exception(e)
                    if time.time() > last_ping + 60:
                        warn("giving up")
                        raise KeyboardInterrupt("Ping timeout")
            except Exception, e:
                warn("Got exception during main monitor thread")
                logging.exception(e)
    finally:
        info("stopping")
        stop()


if __name__ == '__main__':
    main()
