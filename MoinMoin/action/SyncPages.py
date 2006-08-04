# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - SyncPages action

    This action allows you to synchronise pages of two wikis.

    @copyright: 2006 MoinMoin:AlexanderSchremmer
    @license: GNU GPL, see COPYING for details.
"""

import os
import re
import zipfile
import xmlrpclib
from datetime import datetime

# Compatiblity to Python 2.3
try:
    set
except NameError:
    from sets import Set as set


from MoinMoin import wikiutil, config, user
from MoinMoin.packages import unpackLine, packLine
from MoinMoin.PageEditor import PageEditor
from MoinMoin.Page import Page
from MoinMoin.wikidicts import Dict, Group

# directions
UP, DOWN, BOTH = range(3)
directions_map = {"up": UP, "down": DOWN, "both": BOTH}


def normalise_pagename(page_name, prefix):
    if prefix:
        if not page_name.startswith(prefix):
            return None
        else:
            return page_name[len(prefix):]
    else:
        return page_name


class ActionStatus(Exception): pass

class UnsupportedWikiException(Exception): pass

# Move these classes to MoinMoin.wikisync
class SyncPage(object):
    """ This class represents a page in (another) wiki. """
    def __init__(self, name, local_rev=None, remote_rev=None, local_name=None, remote_name=None):
        self.name = name
        self.local_rev = local_rev
        self.remote_rev = remote_rev
        self.local_name = local_name
        self.remote_name = remote_name
        assert local_rev or remote_rev
        assert local_name or remote_name

    def __repr__(self):
        return repr("<Remote Page %r>" % unicode(self))

    def __unicode__(self):
        return u"%s<%r:%r>" % (self.name, self.local_rev, self.remote_rev)

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if not isinstance(other, SyncPage):
            return false
        return self.name == other.name

    def filter(cls, sp_list, func):
        return [x for x in sp_list if func(x.name)]
    filter = classmethod(filter)

    def merge(cls, local_list, remote_list):
        # map page names to SyncPage objects :-)
        d = dict(zip(local_list, local_list))
        for sp in remote_list:
            if sp in d:
                d[sp].remote_rev = sp.remote_rev
                d[sp].remote_name = sp.remote_name
            else:
                d[sp] = sp
        return d.keys()
    merge = classmethod(merge)

    def is_only_local(self):
        return not self.remote_rev

    def is_only_remote(self):
        return not self.local_rev

    def is_local_and_remote(self):
        return self.local_rev and self.remote_rev

    def iter_local_only(cls, sp_list):
        for x in sp_list:
            if x.is_only_local():
                yield x
    iter_local_only = classmethod(iter_local_only)

    def iter_remote_only(cls, sp_list):
        for x in sp_list:
            if x.is_only_remote():
                yield x
    iter_remote_only = classmethod(iter_remote_only)

    def iter_local_and_remote(cls, sp_list):
        for x in sp_list:
            if x.is_local_and_remote():
                yield x
    iter_local_and_remote = classmethod(iter_local_and_remote)

class RemoteWiki(object):
    """ This class should be the base for all implementations of remote wiki
        classes. """

    def __repr__(self):
        """ Returns a representation of the instance for debugging purposes. """
        return NotImplemented

    def get_interwiki_name(self):
        """ Returns the interwiki name of the other wiki. """
        return NotImplemented

    def get_pages(self):
        """ Returns a list of SyncPage instances. """
        return NotImplemented


class MoinRemoteWiki(RemoteWiki):
    """ Used for MoinMoin wikis reachable via XMLRPC. """
    def __init__(self, request, interwikiname, prefix):
        self.request = request
        self.prefix = prefix
        _ = self.request.getText

        wikitag, wikiurl, wikitail, wikitag_bad = wikiutil.resolve_wiki(self.request, '%s:""' % (interwikiname, ))
        self.wiki_url = wikiutil.mapURL(self.request, wikiurl)
        self.valid = not wikitag_bad
        self.xmlrpc_url = self.wiki_url + "?action=xmlrpc2"
        if not self.valid:
            self.connection = None
            return

        self.connection = self.createConnection()

        version = self.connection.getMoinVersion()
        if not isinstance(version, (tuple, list)):
            raise UnsupportedWikiException(_("The remote version of MoinMoin is too old, the version 1.6 is required at least."))

        remote_interwikiname = self.get_interwiki_name()
        remote_iwid = self.connection.interwikiName()[1]
        self.is_anonymous = remote_interwikiname is None
        if not self.is_anonymous and interwikiname != remote_interwikiname:
            raise UnsupportedWikiException(_("The remote wiki uses a different InterWiki name (%(remotename)s)"
                                             " internally than you specified (%(localname)s).") % {
                "remotename": wikiutil.escape(remote_interwikiname), "localname": wikiutil.escape(interwikiname)})

        if self.is_anonymous:
            self.iwid_full = packLine([remote_iwid])
        else:
            self.iwid_full = packLine([remote_iwid, interwikiname])

    def createConnection(self):
        return xmlrpclib.ServerProxy(self.xmlrpc_url, allow_none=True, verbose=True)

    # Methods implementing the RemoteWiki interface
    def get_interwiki_name(self):
        return self.connection.interwikiName()[0]

    def get_pages(self):
        pages = self.connection.getAllPagesEx({"include_revno": True, "include_deleted": True})
        rpages = []
        for name, revno in pages:
            normalised_name = normalise_pagename(name, self.prefix)
            if normalised_name is None:
                continue
            rpages.append(SyncPage(normalised_name, remote_rev=revno, remote_name=name))
        return rpages

    def __repr__(self):
        return "<MoinRemoteWiki wiki_url=%r valid=%r>" % (self.wiki_url, self.valid)


class MoinLocalWiki(RemoteWiki):
    """ Used for the current MoinMoin wiki. """
    def __init__(self, request, prefix):
        self.request = request
        self.prefix = prefix

    def getGroupItems(self, group_list):
        """ Returns all page names that are listed on the page group_list. """
        pages = []
        for group_pagename in group_list:
            pages.extend(Group(self.request, group_pagename).members())
        return [self.createSyncPage(x) for x in pages]

    def createSyncPage(self, page_name):
        normalised_name = normalise_pagename(page_name, self.prefix)
        if normalised_name is None:
            return None
        return SyncPage(normalised_name, local_rev=Page(self.request, page_name).get_real_rev(), local_name=page_name)

    # Methods implementing the RemoteWiki interface
    def get_interwiki_name(self):
        return self.request.cfg.interwikiname

    def get_pages(self):
        return [x for x in [self.createSyncPage(x) for x in self.request.rootpage.getPageList(exists=0)] if x]

    def __repr__(self):
        return "<MoinLocalWiki>"


class ActionClass:
    def __init__(self, pagename, request):
        self.request = request
        self.pagename = pagename
        self.page = Page(request, pagename)

    def parse_page(self):
        options = {
            "remotePrefix": "",
            "localPrefix": "",
            "remoteWiki": "",
            "pageMatch": None,
            "pageList": None,
            "groupList": None,
            "direction": "foo", # is defaulted below
        }

        options.update(Dict(self.request, self.pagename).get_dict())

        # Convert page and group list strings to lists
        if options["pageList"] is not None:
            options["pageList"] = unpackLine(options["pageList"], ",")
        if options["groupList"] is not None:
            options["groupList"] = unpackLine(options["groupList"], ",")

        options["direction"] = directions_map.get(options["direction"], BOTH)

        return options

    def fix_params(self, params):
        """ Does some fixup on the parameters. """

        # merge the pageList case into the pageMatch case
        if params["pageList"] is not None:
            params["pageMatch"] = u'|'.join([r'^%s$' % re.escape(name)
                                             for name in params["pageList"]])
            del params["pageList"]

        if params["pageMatch"] is not None:
            params["pageMatch"] = re.compile(params["pageMatch"], re.U)

        # we do not support matching or listing pages if there is a group of pages
        if params["groupList"]:
            params["pageMatch"] = None

        return params

    def render(self):
        """ Render action

        This action returns a status message.
        """
        _ = self.request.getText

        params = self.fix_params(self.parse_page())

        try:
            if not self.request.cfg.interwikiname:
                raise ActionStatus(_("Please set an interwikiname in your wikiconfig (see HelpOnConfiguration) to be able to use this action."))

            if not params["remoteWiki"]:
                raise ActionStatus(_("Incorrect parameters. Please supply at least the ''remoteWiki'' parameter."))

            local = MoinLocalWiki(self.request, params["localPrefix"])
            try:
                remote = MoinRemoteWiki(self.request, params["remoteWiki"], params["remotePrefix"])
            except UnsupportedWikiException, (msg, ):
                raise ActionStatus(msg)

            if not remote.valid:
                raise ActionStatus(_("The ''remoteWiki'' is unknown."))

            self.sync(params, local, remote)
        except ActionStatus, e:
            return self.page.send_page(self.request, msg=u'<p class="error">%s</p>\n' % (e.args[0], ))

        return self.page.send_page(self.request, msg=_("Syncronisation finished."))
    
    def sync(self, params, local, remote):
        """ This method does the syncronisation work. """
        
        r_pages = remote.get_pages()
        l_pages = local.get_pages()

        if params["groupList"]:
            pages_from_groupList = set(local.getGroupItems(params["groupList"]))
            r_pages = SyncPage.filter(r_pages, pages_from_groupList.__contains__)
            l_pages = SyncPage.filter(l_pages, pages_from_groupList.__contains__)

        m_pages = SyncPage.merge(l_pages, r_pages)

        print "Got %i local, %i remote pages, %i merged pages" % (len(l_pages), len(r_pages), len(m_pages))
        
        if params["pageMatch"]:
            m_pages = SyncPage.filter(m_pages, params["pageMatch"].match)
        print "After filtering: Got %i merges pages" % (len(m_pages), )

        on_both_sides = list(SyncPage.iter_local_and_remote(m_pages))
        remote_but_not_local = list(SyncPage.iter_remote_only(m_pages))
        local_but_not_remote = list(SyncPage.iter_local_only(m_pages))
        
        # some initial test code
        r_new_pages = u", ".join([unicode(x) for x in remote_but_not_local])
        l_new_pages = u", ".join([unicode(x) for x in local_but_not_remote])
        raise ActionStatus("These pages are in the remote wiki, but not local: " + wikiutil.escape(r_new_pages) + "<br>These pages are in the local wiki, but not in the remote one: " + wikiutil.escape(l_new_pages))
        #if params["direction"] in (DOWN, BOTH):
        #    for rp in remote_but_not_local:
                # XXX add locking, acquire read-lock on rp
                


def execute(pagename, request):
    ActionClass(pagename, request).render()
