# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - This is just a sample for a xmlrpc plugin

    @copyright: 2005 by Thomas Waldmann (MoinMoin:ThomasWaldmann)
    @license: GNU GPL, see COPYING for details.
"""

def execute(xmlrpcobj, *args):
    str = args[0]
    return xmlrpcobj._outstr("Hello World!\n" + str)

