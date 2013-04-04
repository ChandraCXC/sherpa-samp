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
import re


__all__ = ('decode_string', 'encode_string', 'capture_exception', 'DictionaryClass')

first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')

def convert(name):
    s0 = name.replace("-", "_")
    s1 = first_cap_re.sub(r'\1_\2', s0)
    return all_cap_re.sub(r'\1_\2', s1).lower()


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

class DictionaryClass(object):
    def __init__(self, obj):
        
        for k, v in obj.iteritems():
          if isinstance(v, dict):
            setattr(self, convert(k), DictionaryClass(v))
          elif isinstance(v, list):
            newlist = list()
            for i in range(len(v)):
                elem = v.pop()
                if isinstance(elem, dict):
                    newlist.append(DictionaryClass(elem))
                else:
                    newlist.append(elem)
            setattr(self, convert(k), newlist)
          else:
            setattr(self, convert(k), v)

    def __getitem__(self, val):
        return self.__dict__[val]
  
    def __repr__(self):
        return '{%s}' % str(', '.join('%s : %s' % (k, repr(v)) for
          (k, v) in self.__dict__.iteritems()))
          
    def get_dict(self):
        resp = {}
        for k,v in self.__dict__.iteritems():
            if isinstance(v, DictionaryClass):
                resp[k] = v.get_dict()
            else:
                resp[k] = v
        return resp
