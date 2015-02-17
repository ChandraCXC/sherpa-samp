#!/usr/bin/env python
#
#  Copyright (C) 2015  Smithsonian Astrophysical Observatory
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
import sedstacker



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


def redshift(stack, z0, correct_flux):

    for seg in stack:
        if numpy.isnan(seg.z):
            seg.z = None

    shifted_stack = stack.shift(z0, correct_flux=correct_flux)

    return shifted_stack


def stack(stack, binsize, statistic, smooth, smooth_binsize, logbin):
    stacked_sed = sedstacker.sed.stack(stack, binsize, statistic,
                                       fill='remove', smooth=smooth,
                                       smooth_binsize=smooth_binsize,
                                       logbin=logbin)
    return stacked_sed