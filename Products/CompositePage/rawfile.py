##############################################################################
#
# Copyright (c) 2002 Zope Foundation and Contributors.
# All Rights Reserved.
# 
# This software is subject to the provisions of the Zope Public License,
# Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
# 
##############################################################################
"""Binary data that is stored in a file.

$Id: rawfile.py,v 1.3 2004/04/03 16:35:32 shane Exp $
"""

import os
from os import stat
from time import time

import Acquisition
from Acquisition import aq_inner, aq_parent
import Globals
from Globals import package_home
from App.Common import rfc1123_date
from DateTime import DateTime


class RawFile(Acquisition.Explicit):
    """Binary data stored in external files."""

    def __init__(self, path, content_type, _prefix=None):
        if _prefix is None:
            _prefix = SOFTWARE_HOME
        elif type(_prefix) is not type(''):
            _prefix = package_home(_prefix)
        path = os.path.join(_prefix, path)
        self.path = path
        self.cch = 'public, max-age=3600'  # One hour

        file = open(path, 'rb')
        data = file.read()
        file.close()
        self.content_type = content_type
        self.__name__ = path.split('/')[-1]
        self.lmt = float(stat(path)[8]) or time()
        self.lmh = rfc1123_date(self.lmt)


    def __call__(self, REQUEST=None, RESPONSE=None):
        """Default rendering"""
        # HTTP If-Modified-Since header handling. This is duplicated
        # from OFS.Image.Image - it really should be consolidated
        # somewhere...
        if RESPONSE is not None:
            RESPONSE.setHeader('Content-Type', self.content_type)
            RESPONSE.setHeader('Last-Modified', self.lmh)
            RESPONSE.setHeader('Cache-Control', self.cch)
            if REQUEST is not None:
                header = REQUEST.get_header('If-Modified-Since', None)
                if header is not None:
                    header = header.split(';')[0]
                    # Some proxies seem to send invalid date strings for this
                    # header. If the date string is not valid, we ignore it
                    # rather than raise an error to be generally consistent
                    # with common servers such as Apache (which can usually
                    # understand the screwy date string as a lucky side effect
                    # of the way they parse it).
                    try:
                        mod_since = long(DateTime(header).timeTime())
                    except:
                        mod_since = None
                    if mod_since is not None:
                        if getattr(self, 'lmt', None):
                            last_mod = long(self.lmt)
                        else:
                            last_mod = long(0)
                        if last_mod > 0 and last_mod <= mod_since:
                            RESPONSE.setStatus(304)
                            return ''

        f = open(self.path, 'rb')
        data = f.read()
        f.close()
        data = self.interp(data)
        return data

    def interp(self, data):
        """Hook point for subclasses that modify the file content.
        """
        return data

    index_html = None  # Tells ZPublisher to use __call__

    HEAD__roles__ = None
    def HEAD(self, REQUEST, RESPONSE):
        """ """
        RESPONSE.setHeader('Content-Type', self.content_type)
        RESPONSE.setHeader('Last-Modified', self.lmh)
        return ''


class InterpolatedFile(RawFile):
    """Text data, stored in a file, with %(xxx)s interpolation.
    """

    def interp(self, data):
        parent_url = aq_parent(aq_inner(self)).absolute_url()
        d = {
            "parent_url": parent_url,
            }
        return data % d

