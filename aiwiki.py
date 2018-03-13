# -*- coding: utf-8 -*-

from farmconfig import FarmConfig

class Config(FarmConfig):
    sitename = u'The AI Wiki'
    interwikiname = 'aiwiki'
    show_interwiki = False
    logo_string = u'<img src="/moin_static198/common/aiwiki_64.png" alt="AI Wiki Logo"><h4 id="The_AI_Wiki">The AI Wiki</h4>'
    acl_rights_before = u"+All:read"
    acl_rights_default = u"admin:write,delete,revert,admin Known:write +AdminGroup:admin,delete"

    page_front_page = u"Home" 
    
    data_dir = '/var/www/moin/aiwiki/data/'
    data_underlay_dir = '/var/www/moin/aiwiki/underlay/'
    cache_dir = '/var/lib/moin/cache'
    user_checkbox_defaults = {'show_page_trail':False}

    surge_action_limits = { # allow max. <count> <action> requests per <dt> secs
        # action: (count, dt)
        'show': (20, 60),
        'raw': (20, 40),  # some people use this for css
        'AttachFile': (60, 60),
        'diff': (30, 60),
        'fullsearch': (5, 60),
        'edit': (30, 120),
        'rss_rc': (1, 60),
        'default': (30, 60),
    }
    surge_lockout_time = 3600 # secs you get locked out when you ignore warnings

    superuser = ['admin','AndreyK']
    theme_default = u"hal"
    trail_size = 0

    mail_from = u"MoinMoin notifier <admin@example.com>"
    mail_smarthost = "127.0.0.1"

    editor_force = False
    editor_default = 'gui'
    editor_ui = 'freechoice'

    secrets = '72451f66a0e31a454c01d6c3cedca46a6946b567796d333073906a792549e2a2'
    secrets = '00c56057b27790305f4bf76bd0e0180e670e3a817b97c0e95b92d727e79206f5'
