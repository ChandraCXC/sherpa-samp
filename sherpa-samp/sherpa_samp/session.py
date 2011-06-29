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


import numpy
import sherpa.all
import sherpa.astro.all
import sherpa.astro.ui as sherpaUI

import logging
logger = logging.getLogger(__name__)
info = logger.info

from sherpa_samp.utils import encode_string, decode_string

__all__ = ("SherpaSession",)

#
## Sherpa Session Object
#

class SherpaSession(object):

    def __init__(self, msg_id=None, mtype=None):
        session = sherpaUI.utils.Session()
        session._add_model_types(sherpa.models.basic)
        session._add_model_types(sherpa.astro.models)
        session._add_model_types(sherpa.instrument,
                                 baselist=(sherpa.models.Model,))
        session._add_model_types(sherpa.astro.instrument)
        session._add_model_types(sherpa.astro.optical)
        #session._add_model_types(sherpa.astro.xspec,
        #                         (sherpa.astro.xspec.XSAdditiveModel,
        #                          sherpa.astro.xspec.XSMultiplicativeModel))
        self.session = session
        self.msg_id = msg_id
        self.mtype = mtype

        # max_rstat of 3 is unhelpful in SED fitting.
        self.session.set_conf_opt("max_rstat", 1.e+38)

        # compute 90% confidence limits by default
        self.session.set_conf_opt("sigma", 1.6448536269514722)


    def set_data(self, datamaps):
        if not numpy.iterable(datamaps):
            raise TypeError("datamaps is not iterable")
        #keys = ["x", "y", "staterror", "syserror", "weights"]
        keys = ["x", "y", "staterror", "syserror"]
        for ii, data in enumerate(datamaps):
            for key in keys:
                if data.has_key(key):
                    data[key] = decode_string(data[key])
                    info('decoding' + key)

            self.session.set_data(ii, sherpa.data.Data1D(**data))

            d = self.session.get_data(ii)
            numpy.set_printoptions(precision=4, threshold=6)
            info("DataSet %i x: " % ii + numpy.array2string(d.x))
            info("DataSet %i y: " % ii + numpy.array2string(d.y))
            info("DataSet %i staterror: " % ii + numpy.array2string(d.staterror))


    def set_model(self, modelmaps):

        self.session._model_components={}

        for ii, model in enumerate(modelmaps):
            if model["name"].strip() == '':
                raise TypeError("Model expression not found")

            self.session.set_model(ii, model["name"])
            info("Model: " + str(ii) + str(self.session.get_source(ii)))


    def set_parameters(self, modelmaps):
        for ii, model in enumerate(modelmaps):
            for component in model["parts"]:

                if component["name"].strip() == '':
                    raise TypeError("Model expression not found")

                mdl = self.session._eval_model_expression(component["name"])
                for pardict in component["pars"]:

                    if pardict["name"].strip() == '':
                        raise TypeError("Model component name missing")

                    par = self.session.get_par(pardict["name"])
                    parname = pardict.pop("name").split(".")[1]

                    # Specview sends parameter attributes as strings,
                    # convert to floats here.  
                    #for attrname in ['val', 'min', 'max']:
                    for attrname in ['val']:
                        if pardict.has_key(attrname):
                            pardict[attrname] = float(pardict[attrname])

                    #pardict.pop('min', None)
                    #pardict.pop('max', None)
                    pardict.pop('alwaysfrozen', None)

                    attrname = 'frozen'
                    if pardict.has_key(attrname):
                        pardict[attrname] = bool(int(pardict[attrname]))

                    par.set(**pardict)
                    info('setting ' + parname + ' with ' + str(pardict))

                info(str(mdl))


    def set_stat(self, statmap):
        self.session.set_stat(statmap["name"])

        # FIXME: A kludge when Specview passes all zeros for staterror
        # for NED SEDs.

        # check for zeros in uncertainties when using leastsq
        if statmap["name"] == "leastsq":
            for ii in self.session.list_data_ids():
                data = self.session.get_data(ii)
                if(data.staterror is not None and
                   (True in (data.staterror <= 0.0))):
                    #data.staterror = numpy.ones_like(data.staterror)
                    data.staterror = numpy.ones_like(data.y)

        info(statmap["name"] + ": " + self.session.get_stat_name())


    def set_method(self, methodmap):
        self.session.set_method(methodmap["name"])
        info(methodmap["name"] + ": ")
        configdict = methodmap.get("config", None)
        if configdict is not None:
            info(methodmap["name"] + ": " + str(methodmap["config"]))
            for key in configdict:
                if str(configdict[key]).startswith('INDEF'):
                    configdict[key] = None
                self.session.set_method_opt(key, configdict[key])
        info(str(self.session.get_method_opt()))


    def set_confidence(self, confidencemap):
        methodname = confidencemap["name"].strip().lower()
        method_opt = getattr(self.session, 'set_%s_opt' % methodname)
        info(confidencemap["name"] + ": ")
        configdict = confidencemap.get("config", None)
        if configdict is not None:
            info(confidencemap["name"] + ": " + str(confidencemap["config"]))
            for key in configdict:
                if str(configdict[key]).startswith('INDEF'):
                    configdict[key] = None
                method_opt(key, configdict[key])
        method_opt = getattr(self.session, 'get_%s_opt' % methodname)
        info(str(method_opt()))


    def get_confidence(self, confidencemap):
        methodname = confidencemap["name"].strip().lower()
        method = getattr(self.session, 'get_%s' % methodname)
        return method()


    def get_flux(self, fluxtype):
        flux_func = getattr(self.session, 'calc_%s_flux' % fluxtype)
        return flux_func


    def run_confidence(self, confidencemap):
        methodname = confidencemap["name"].strip().lower()
        method = getattr(self.session, methodname)
        method()


    def get_confidence_results(self, confidencemap, confidence_results=None):
        if confidence_results is None:
            methodname = confidencemap["name"].strip().lower()
            method_result = getattr(self.session, 'get_%s_results' % methodname)
            confidence_results = method_result()
        results = {}
        results["sigma"]    = repr(float(confidence_results.sigma))
        results["percent"]  = repr(float(confidence_results.percent))
        results["parnames"] = list(confidence_results.parnames)
        results["parvals"]  = encode_string(confidence_results.parvals)
        results["parmins"]  = encode_string(confidence_results.parmins)
        results["parmaxes"] = encode_string(confidence_results.parmaxes)
        return results


    def get_fit_results(self, fit_results=None):
        if fit_results is None:
            fit_results = self.session.get_fit_results()
        results = {}
        results["succeeded"] = str(int(bool(fit_results.succeeded)))
        results["parvals"]   = encode_string(fit_results.parvals)
        results["parnames"]  = list(fit_results.parnames)
        results["statval"]   = repr(float(fit_results.statval))
        results["numpoints"] = str(int(fit_results.numpoints))
        results["dof"]       = repr(float(fit_results.dof))

        results["qval"]      = 'nan'
        if fit_results.qval is not None:
            results["qval"]  = repr(float(fit_results.qval))

        results["rstat"]     = 'nan'
        if fit_results.rstat is not None:
            results["rstat"] = repr(float(fit_results.rstat))

        results["nfev"]      = str(int(fit_results.nfev))
        return results
