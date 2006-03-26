#
# Makefile for MoinMoin
#

testwiki := ./testwiki
share := ./wiki

all:
	python setup.py build

install-docs:
	-mkdir build
	wget -U MoinMoin/Makefile -O build/INSTALL.html "http://moinmaster.wikiwikiweb.de/MoinMoin/InstallDocs?action=print"
	sed \
		-e 's#href="/#href="http://moinmaster.wikiwikiweb.de/#g' \
		-e 's#http://[a-z\.]*/wiki/classic/#/wiki/classic/#g' \
		-e 's#http://[a-z\.]*/wiki/modern/#/wiki/modern/#g' \
		-e 's#http://[a-z\.]*/wiki/rightsidebar/#/wiki/rightsidebar/#g' \
		-e 's#/wiki/classic/#wiki/htdocs/classic/#g' \
		-e 's#/wiki/modern/#wiki/htdocs/modern/#g' \
		-e 's#/wiki/rightsidebar/#wiki/htdocs/rightsidebar/#g' \
        build/INSTALL.html >docs/INSTALL.html
	-rm build/INSTALL.html

	-rmdir build

interwiki:
	wget -U MoinMoin/Makefile -O $(share)/data/intermap.txt "http://moinmaster.wikiwikiweb.de/InterWikiMap?action=raw"
	chmod 664 $(share)/data/intermap.txt

check-tabs:
	@python -c 'import tabnanny ; tabnanny.check("MoinMoin")'

# Create documentation
epydoc: patchlevel
	@MoinMoin/version.py update
	@epydoc -o ../html -n MoinMoin -u http://moinmoin.wikiwikiweb.de MoinMoin

# Create new underlay directory from MoinMaster
# Should be used only on TW machine
underlay:
	rm -rf $(share)/underlay
	MoinMoin/script/moin.py --config-dir=/srv/de.wikiwikiweb.moinmaster/bin15 --wiki-url=moinmaster.wikiwikiweb.de/ maint reducewiki --target-dir=$(share)/underlay
	rm -rf $(share)/underlay/pages/InterWikiMap/
	echo -ne "#acl All:read\r\nSee MoinMoin:EditingOnMoinMaster.\r\n" > \
	    $(share)/underlay/pages/MoinPagesEditorGroup/revisions/00000001
	cd $(share); rm -rf underlay.tar.bz2; tar cjf underlay.tar.bz2 underlay

pagepacks:
	@python tests/maketestwiki.py
	@python MoinMoin/scripts/packages/create_pagepacks.py
	cd $(share) ; rm -rf underlay
	cp -a $(testwiki)/underlay $(share)/
	
dist:
	-rm MANIFEST
	python setup.py sdist

# Create patchlevel module
patchlevel:
	@echo -e patchlevel = "\"`tla logs | tail -n1`\"\n" >MoinMoin/patchlevel.py

# Report translations status
check-i18n:
	MoinMoin/i18n/check_i18n.py

# Update the current tree from `tla my-default-archive`
update:
	tla update
	$(MAKE) patchlevel

# Update underlay directory from the tarball
update-underlay:
	cd $(share); rm -rf underlay; tar xjf underlay.tar.bz2

# Merge from main branch
# Ignore error in the merge and update underlay
merge:
	tla star-merge arch@arch.thinkmo.de--2003-archives/moin--main--1.3

test: 
	@python tests/maketestwiki.py
	@python tests/runtests.py

clean: clean-testwiki clean-pyc
	rm -rf build

clean-testwiki:
	rm -rf $(testwiki)/*

clean-pyc:
	find . -name "*.pyc" -exec rm -rf "{}" \; 

.PHONY: all dist install-docs check-tabs epydoc underlay patchlevel \
	check-i18n update update-underlay merge test testwiki clean \
	clean-testwiki clean-pyc

