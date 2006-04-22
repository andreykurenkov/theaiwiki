# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - Load I18N Text

    This macro has the main purpose of supporting Help* page authors
    to insert the texts that a user actually sees on his screen into
    the description of the related features (which otherwise could
    get very confusing).

    @copyright: 2001 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

from MoinMoin import wikiutil

Dependencies = ["language"]

def execute(macro, args):
    """ Return a translation of args, or args as is """
    translation = macro.request.getText(args, formatted=False)

    return macro.formatter.text(translation)

