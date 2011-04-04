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
import base64
import traceback
import cStringIO


__all__ = ('decode_string', 'encode_string', 'capture_exception')


def decode_string(encoded_string, dtype="<f8"):

    decoded_string = base64.b64decode(encoded_string)
    array = numpy.fromstring(decoded_string, dtype=numpy.float64).byteswap()
    # array = numpy.ndarray(shape, dtype, decoded_string)
    return array


def encode_string(array, dtype="<f8"):

    array = numpy.asarray(array, dtype=numpy.float64)
    decoded_string = array.byteswap().tostring()
    encoded_string = base64.b64encode(decoded_string)
    return encoded_string



def capture_exception():
    trace = cStringIO.StringIO()
    traceback.print_exc(limit=None, file=trace)
    value = trace.getvalue()
    trace.close()
    return value

