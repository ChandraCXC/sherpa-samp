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


__all__ = ('SEDException','DataException','ModelException','FitException','ConfidenceException','ParameterException','StatisticException','MethodException')





class SEDException(Exception):

    def __init__(self, msg=''):
        Exception.__init__(self, msg)


class DataException(SEDException):

    def __init__(self, msg=''):
        SEDException.__init__(self, msg)




class ModelException(SEDException):

    def __init__(self, msg=''):
        SEDException.__init__(self, msg)




class FitException(SEDException):

    def __init__(self, msg=''):
        SEDException.__init__(self, msg)




class ConfidenceException(SEDException):

    def __init__(self, msg=''):
        SEDException.__init__(self, msg)




class ParameterException(SEDException):

    def __init__(self, msg=''):
        SEDException.__init__(self, msg)




class StatisticException(SEDException):

    def __init__(self, msg=''):
        SEDException.__init__(self, msg)




class MethodException(SEDException):

    def __init__(self, msg=''):
        SEDException.__init__(self, msg)



