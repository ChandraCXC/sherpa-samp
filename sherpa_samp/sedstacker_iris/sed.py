#!/usr/bin/env python

import logging

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(levelname)s:%(message)s')
hndlr = logging.StreamHandler()
logger.addHandler(hndlr)


def normalize(stack, payload):
    add_or_mult = payload.add_or_mult
    correct_flux = payload.correct_flux
    correct_flux = False
    z0 = payload.z0
    z0 = None
    y0 = payload.y0
    x0 = payload.x0
    ytype = payload.ytype
    min_wave = payload.xmin
    max_wave = payload.xmax
    if isinstance(min_wave, basestring):
        min_wave = min_wave.lower()
    if isinstance(max_wave, basestring):
        max_wave = max_wave.lower()

    if not payload.integrate:
        try:
            norm_stack = stack.normalize_at_point(x0, y0, norm_operator=add_or_mult, stats=ytype,
                                                  correct_flux=correct_flux, z0=z0)
            return norm_stack
        except Exception, ex:
            logger.warning(ex)
            return None
    else:
        try:
            norm_stack = stack.normalize_by_int(minWavelength=min_wave, maxWavelength=max_wave, stats=ytype,
                                                y0=y0, norm_operator=add_or_mult, correct_flux=correct_flux,
                                                z0=z0)
            return norm_stack
        except Exception, ex:
            logger.warning(ex)
            return None
