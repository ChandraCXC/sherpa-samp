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
from __future__ import division

__all__ = ('Sed')

__author__="olaurino"
__date__ ="$Feb 4, 2013 5:05:26 PM$"

from astLib.astSED import SED as astSed
from numpy import trapz, array, logspace, linspace, ceil, floor, log10

class Sed(astSed):
    """
    This class extends the astLib.astSED.SED class
    for the more general case of aggregated SEDs.
    
    This class is meant to be a support for some sherpa operations, but it
    doesn't even attempt to be a comprehensive SED class.
    """
    
    def __init__(self, wavelength, flux, z=0.0):
        """
        The difference between this constructor and the astLib one
        is that z has different semantics here, being the redhisft of the source,
        if any. If z is not provided, wavelength and flux are just passed to
        the parent class's constructor. Otherwise, the wavelength and flux are 
        shifted to the rest frame and passed to the parent's constructor along with z
        """
        if z==0.0:
            astSed.__init__(self, wavelength, flux)
            return
        
        wavelength = array(wavelength)
        flux = array(flux)
        
        wavelength_z0 = wavelength/(1+z)
        
        z0_total_flux = trapz(wavelength_z0, flux)
        z_total_flux = trapz(wavelength, flux)
        
        flux_z0 = flux*z_total_flux/z0_total_flux
        
        astSed.__init__(self, wavelength_z0, flux_z0, z)
        
    def interpolate(self, function, interval, num_bins, log):
        """
        Use function to interpolate this sed in a defined interval divided into
        num_bins bins.
        
        Function must take argument xout, xin, yin and return an yout array.
        """
        
        
        if log:
            xmin=floor(log10(interval[0]))
            xmax=ceil(log10(interval[1]))
            bins=logspace(xmin, xmax, num_bins, endpoint=True)
        else:
            xmin=interval[0]
            xmax=interval[1]
            bins=linspace(xmin, xmax, num_bins, endpoint=True)
        flux=function(log10(bins), log10(self.wavelength), log10(self.flux))
        return Sed(bins, 10**flux)
        
    
