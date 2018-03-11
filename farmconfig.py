# -*- coding: iso-8859-1 -*-

wikis = [
    ("aiwiki",  r"^.*$"),
]

from MoinMoin.config.multiconfig import DefaultConfig

class FarmConfig(DefaultConfig):

    data_underlay_dir = '/test/wikifarm/underlay/'
    

