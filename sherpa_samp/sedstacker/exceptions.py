#!/usr/bin/env python


class SedStackerException(Exception):

    def __init__(self, msg=''):
        Exception.__init__(self, msg)


class RedshiftException(SedStackerException):

    def __init__(self, msg=''):
        SedStackerException.__init__(self, msg)


class SegmentErrorException(SedStackerException):

    def __init__(self, msg=''):
        SedStackerException.__init__(self, msg)




