# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - per page hit statistics

    @copyright: 2004-2005 ThomasWaldmann (MoinMoin:ThomasWaldmann)
    @license: GNU GPL, see COPYING for details

"""

try:
    import cPickle as pickle
except ImportError:
    import pickle

# Set pickle protocol, see http://docs.python.org/lib/node64.html
PICKLE_PROTOCOL = pickle.HIGHEST_PROTOCOL

from MoinMoin import caching, config
from MoinMoin.Page import Page
from MoinMoin.logfile import eventlog, logfile


class PageHits:
    
    def __init__(self, macro, args):
        self.macro = macro
        self.request = macro.request
        self.cache = cache = caching.CacheEntry(self.request, 'charts', 'pagehits', scope='wiki')

    def execute(self):
        """ Execute the macro and return output """
        cacheDate, hits = self.cachedHits()
        self.addHitsFromLog(hits, cacheDate)
        self.filterReadableHits(hits)
        hits = [(hits[pagename], pagename) for pagename in hits]
        hits.sort()
        hits.reverse()
        return self.format(hits)
        
    def cachedHits(self):
        """ Return tuple (cache date, cached hits) for all pages """
        date, hits = 0, {}        
        if self.cache.exists():
            try:
                date, hits = pickle.loads(self.cache.content())
            except (pickle.UnpicklingError, IOError, EOFError, ValueError):
                self.cache.remove()
        return date, hits

    def addHitsFromLog(self, hits, cacheDate):
        """ Parse the log, add hits after cacheDate and update the cache """
        event_log = eventlog.EventLog(self.request)
        try:
            logDate = event_log.date()
        except logfile.LogMissing:
            return
            
        changed = False
        event_log.set_filter(['VIEWPAGE'])
        for event in event_log.reverse():
            if event[0] <= cacheDate:
                break
            page = event[2].get('pagename', None)
            if page:
                hits[page] = hits.get(page, 0) + 1
                changed = True
        
        if changed:
            self.updateCache(logDate, hits) 
        
    def updateCache(self, date, hits):
        self.cache.update(pickle.dumps((date, hits), PICKLE_PROTOCOL))
    
    def filterReadableHits(self, hits):
        """ Filter out hits the user many not see """
        userMayRead = self.request.user.may.read
        for pagename in hits.keys():
            page = Page(self.request, pagename)
            if page.exists() and userMayRead(pagename):
                continue
            del hits[pagename]

    def format(self, hits):
        """ Return formated output """
        result = []
        formatter = self.macro.formatter
        result.append(formatter.number_list(1))
        for hit, pagename in hits:
            result.extend([
                formatter.listitem(1),
                formatter.code(1),
                ("%6d" % hit).replace(" ", "&nbsp;"), " ",
                formatter.code(0),
                formatter.pagelink(1, pagename, generated=1),
                formatter.text(pagename),
                formatter.pagelink(0, pagename),
                formatter.listitem(0),
            ])
        result.append(formatter.number_list(0))    
        return ''.join(result)


def execute(macro, args):
    return PageHits(macro, args).execute()
