#!/usr/bin/env python

import logging

logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(levelname)s:%(message)s')
hndlr = logging.StreamHandler()
logger.addHandler(hndlr)


def normalize(stack, payload):
    norm_operator = int(payload.norm_operator)
    # correct_flux = payload.correct_flux
    correct_flux = False
    # z0 = payload.z0
    z0 = None
    y0 = float(payload.y0)
    stats = payload.stats

    if payload.integrate != 'true':
        x0 = float(payload.x0)
        norm_stack = stack.normalize_at_point(x0, y0, norm_operator=norm_operator, stats=stats,
                                              correct_flux=correct_flux, z0=z0)
        return norm_stack
    else:
        if payload.xmin.lower() != 'min':
            minWavelength = float(payload.xmin)
        else:
            minWavelength = payload.xmin.lower()
        if payload.xmax.lower() != 'max':
            maxWavelength = float(payload.xmax)
        else:
            maxWavelength = payload.xmax.lower()
        norm_stack = stack.normalize_by_int(minWavelength=minWavelength, maxWavelength=maxWavelength, stats=stats,
                                            y0=y0, norm_operator=norm_operator, correct_flux=correct_flux,
                                            z0=z0)
        return norm_stack
