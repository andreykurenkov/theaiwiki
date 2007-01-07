# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - msexcel filter

    Depends on: "xls2csv" command from "catdoc" package
    
    @copyright: 2006 by ThomasWaldmann MoinMoin:ThomasWaldmann
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import filter

def execute(indexobj, filename):
    data = filter.execfilter("xls2csv '%s'", filename)
    # xls2csv uses comma as field separator and "field content",
    # we strip both to not confuse the indexer
    data = data.replace(u',', u' ').replace(u'"', u' ')
    return data

