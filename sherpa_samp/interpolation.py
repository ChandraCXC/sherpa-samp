#  Copyright (C) 2013  Smithsonian Astrophysical Observatory
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

__author__="olaurino"
__date__ ="$Feb 4, 2013 11:14:06 PM$"

from scipy import interpolate
from numpy import array, mean

import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                   format='[SHERPA] %(levelname)-8s %(asctime)s %(message)s',
                   datefmt='%a, %d %b %Y %H:%M:%S',
                   filename='SAMPSherpa.log', # FIXME: user permissions!
                   filemode='w')

info = logger.info
warn = logger.warning
error = logger.error

def spline_interp(xout, xin, yin):
    tck = interpolate.splrep(xin, yin, s=0.0)
    return interpolate.splev(xout, tck, der=0)

def interp1d(xout, xin, yin):
    info('interp1d: sorting dataset')
    xin, yin = (list(x) for x in zip(*sorted(zip(xin, yin), key=lambda pair: pair[0])))

    ds={}

    info('interp1d: computing averages')
    for x,y in zip(xin,yin):
        if ds.has_key(x):
            ds[x].append(y)
        else:
            ds[x]=[y,]

    x=[]
    y=[]
    for (k,v) in ds.iteritems():
        x.append(k)
        y.append(mean(v))

    x=array(x)
    y=array(y)

    x, y = (list(xin) for xin in zip(*sorted(zip(x, y), key=lambda pair: pair[0])))
    
    info('interpolating')
    f=interpolate.interp1d(x,y,bounds_error=False,kind='linear')
    return f(xout)
    
    