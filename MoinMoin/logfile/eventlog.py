"""
    MoinMoin event log class
    
    The global event-log is mainly used for statistics (e.g. EventStats).

    @license: GNU GPL, see COPYING for details.
"""

import time

from MoinMoin.logfile import LogFile
from MoinMoin import wikiutil

class EventLog(LogFile):

    def __init__(self, request, filename=None, buffer_size=65536, **kw):
        if filename is None:
            rootpagename = kw.get('rootpagename', None)
            if rootpagename:
                from MoinMoin.Page import Page
                filename = Page(request, rootpagename).getPagePath('event-log', isfile=1)
            else:
                filename = request.rootpage.getPagePath('event-log', isfile=1)
        LogFile.__init__(self, filename, buffer_size)

    def add(self, request, eventtype, values=None, add_http_info=1,
            mtime_usecs=None):
        """ Write an event of type `eventtype, with optional key/value
        pairs appended (i.e. you have to pass a dict).
        """
        if request.isSpiderAgent:
            return

        if mtime_usecs is None:
            mtime_usecs = wikiutil.timestamp2version(time.time())

        if values is None:
            values = {}
        if add_http_info:
            # All these are ascii
            for key in ['remote_addr', 'http_user_agent', 'http_referer']:
                value = getattr(request, key, '')
                if value:
                    # Save those http headers in UPPERcase
                    values[key.upper()] = value
        # Encode values in a query string TODO: use more readable format
        values = wikiutil.makeQueryString(values, want_unicode=True)
        self._add(u"%d\t%s\t%s\n" % (mtime_usecs, eventtype, values))

    def parser(self, line):
        try:
            time_usecs, eventtype, kvpairs = line.rstrip().split('\t')
        except ValueError:
            # badly formatted line in file, skip it
            return None
        return long(time_usecs), eventtype, wikiutil.parseQueryString(kvpairs)

    def set_filter(self, event_types=None):
        if event_types is None:
            self.filter = None
        else:
            self.filter = lambda line: (line[1] in event_types)


