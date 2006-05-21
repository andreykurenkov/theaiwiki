# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - lupy indexing search engine

    @copyright: 2005 by Florian Festi, Nir Soffer, Thomas Waldmann
    @license: GNU GPL, see COPYING for details.
"""

import os, re, codecs, errno, time

from MoinMoin.Page import Page
from MoinMoin import config, wikiutil
from MoinMoin.util import filesys, lock
from MoinMoin.support.lupy.index.term import Term
from MoinMoin.support.lupy import document
from MoinMoin.support.lupy.index.indexwriter import IndexWriter
from MoinMoin.support.lupy.search.indexsearcher import IndexSearcher

from MoinMoin.support.lupy.index.term import Term
from MoinMoin.support.lupy.search.term import TermQuery
from MoinMoin.support.lupy.search.boolean import BooleanQuery

##############################################################################
### Tokenizer
##############################################################################

singleword = r"[%(u)s][%(l)s]+" % {
                 'u': config.chars_upper,
                 'l': config.chars_lower,
             }

singleword_re = re.compile(singleword, re.U)
wikiword_re = re.compile(r"^(%s){2,}$" % singleword, re.U)

token_re = re.compile(
    r"(?P<company>\w+[&@]\w+)|" + # company names like AT&T and Excite@Home.
    r"(?P<email>\w+([.-]\w+)*@\w+([.-]\w+)*)|" +    # email addresses
    r"(?P<hostname>\w+(\.\w+)+)|" +                 # hostnames
    r"(?P<num>(\w+[-/.,])*\w*\d\w*([-/.,]\w+)*)|" + # version numbers
    r"(?P<acronym>(\w\.)+)|" +          # acronyms: U.S.A., I.B.M., etc.
    r"(?P<word>\w+)",                   # words
    re.U)

dot_re = re.compile(r"[-_/,.]")
mail_re = re.compile(r"[-_/,.]|(@)")

def tokenizer(value):
    """Yield a stream of lower cased words from a string."""
    if isinstance(value, list): # used for page links
        for v in value:
            yield v
    else:
        tokenstream = re.finditer(token_re, value)
        for m in tokenstream:
            if m.group("acronym"):
                yield m.group("acronym").replace('.', '').lower()
            elif m.group("company"):
                yield m.group("company").lower()
            elif m.group("email"):
                for word in mail_re.split(m.group("email").lower()):
                    if word:
                        yield word
            elif m.group("hostname"):                
                for word in dot_re.split(m.group("hostname").lower()):
                    yield word
            elif m.group("num"):
                for word in dot_re.split(m.group("num").lower()):
                    yield word
            elif m.group("word"):
                word = m.group("word")
                yield  word.lower()
                # if it is a CamelCaseWord, we additionally yield Camel, Case and Word
                if wikiword_re.match(word):
                    for sm in re.finditer(singleword_re, word):
                        yield sm.group().lower()


#############################################################################
### Indexing
#############################################################################

class UpdateQueue:
    def __init__(self, file, lock_dir):
        self.file = file
        self.writeLock = lock.WriteLock(lock_dir, timeout=10.0)
        self.readLock = lock.ReadLock(lock_dir, timeout=10.0)

    def exists(self):
        return os.path.exists(self.file)

    def append(self, pagename):
        """ Append a page to queue """
        if not self.writeLock.acquire(60.0):
            request.log("can't add %r to lupy update queue: can't lock queue" %
                        pagename)
            return
        try:
            f = codecs.open(self.file, 'a', config.charset)
            try:
                f.write(pagename + "\n")
            finally:
                f.close()                
        finally:
            self.writeLock.release()

    def pages(self):
        """ Return list of pages in the queue """
        if self.readLock.acquire(1.0):
            try:
                return self._decode(self._read())
            finally:
                self.readLock.release()            
        return []

    def remove(self, pages):
        """ Remove pages from the queue
        
        When the queue is empty, the queue file is removed, so exists()
        can tell if there is something waiting in the queue.
        """
        if self.writeLock.acquire(30.0):
            try:
                queue = self._decode(self._read())
                for page in pages:
                    try:
                        queue.remove(page)
                    except ValueError:
                        pass
                if queue:
                    self._write(queue)
                else:
                    self._removeFile()
                return True
            finally:
                self.writeLock.release()
        return False

    # Private -------------------------------------------------------

    def _decode(self, data):
        """ Decode queue data """
        pages = data.splitlines()
        return self._filterDuplicates(pages)

    def _filterDuplicates(self, pages):
        """ Filter duplicates in page list, keeping the order """
        unique = []
        seen = {}
        for name in pages:
            if not name in seen:
                unique.append(name)
                seen[name] = 1
        return unique

    def _read(self):
        """ Read and return queue data
        
        This does not do anything with the data so we can release the
        lock as soon as possible, enabling others to update the queue.
        """
        try:
            f = codecs.open(self.file, 'r', config.charset)
            try:
                return f.read()
            finally:
                f.close()
        except (OSError, IOError), err:
            if err.errno != errno.ENOENT:
                raise
            return ''

    def _write(self, pages):
        """ Write pages to queue file
        
        Requires queue write locking.
        """
        # XXX use tmpfile/move for atomic replace on real operating systems
        data = '\n'.join(pages) + '\n'
        f = codecs.open(self.file, 'w', config.charset)
        try:
            f.write(data)
        finally:
            f.close()            

    def _removeFile(self):
        """ Remove queue file 
        
        Requires queue write locking.
        """
        try:
            os.remove(self.file)
        except OSError, err:
            if err.errno != errno.ENOENT:
                raise


class Index:
    class LockedException(Exception):
        pass
    
    def __init__(self, request):
        self.request = request
        cache_dir = request.cfg.cache_dir
        self.main_dir = os.path.join(cache_dir, 'lupy')
        self.dir = os.path.join(self.main_dir, 'index')
        filesys.makeDirs(self.dir)
        self.sig_file = os.path.join(self.main_dir, 'complete')
        self.segments_file = os.path.join(self.dir, 'segments')
        lock_dir = os.path.join(self.main_dir, 'index-lock')
        self.lock = lock.WriteLock(lock_dir,
                                   timeout=3600.0, readlocktimeout=60.0)
        self.read_lock = lock.ReadLock(lock_dir, timeout=3600.0)
        self.queue = UpdateQueue(os.path.join(self.main_dir, "update-queue"),
                                 os.path.join(self.main_dir, 'update-queue-lock'))
        
        # Disabled until we have a sane way to build the index with a
        # queue in small steps.
        ## if not self.exists():
        ##    self.indexPagesInNewThread(request)

    def exists(self):
        """ Check if index exists """        
        return os.path.exists(self.sig_file)
                
    def mtime(self):
        return os.path.getmtime(self.segments_file)

    def _search(self, query):
        """ read lock must be acquired """
        while True:
            try:
                searcher, timestamp = self.request.cfg.lupy_searchers.pop()
                if timestamp != self.mtime():
                    searcher.close()
                else:
                    break
            except IndexError:
                searcher = IndexSearcher(self.dir)
                timestamp = self.mtime()
                break
            
        hits = list(searcher.search(query))
        self.request.cfg.lupy_searchers.append((searcher, timestamp))
        return hits
    
    def search(self, query):
        if not self.read_lock.acquire(1.0):
            raise self.LockedException
        try:
            hits = self._search(query)
        finally:
            self.read_lock.release()
        return hits

    def update_page(self, page):
        self.queue.append(page.page_name)
        self._do_queued_updates_InNewThread()

    def _do_queued_updates_InNewThread(self):
        """ do queued index updates in a new thread
        
        Should be called from a user request. From a script, use indexPages.
        """
        if not self.lock.acquire(1.0):
            self.request.log("can't index: can't acquire lock")
            return
        try:
            from threading import Thread
            indexThread = Thread(target=self._do_queued_updates,
                args=(self._indexingRequest(self.request), self.lock))
            indexThread.setDaemon(True)
            
            # Join the index thread after current request finish, prevent
            # Apache CGI from killing the process.
            def joinDecorator(finish):
                def func():
                    finish()
                    indexThread.join()
                return func
                
            self.request.finish = joinDecorator(self.request.finish)        
            indexThread.start()
        except:
            self.lock.release()
            raise

    def indexPages(self, files=None, update=True):
        """ Index all pages (and files, if given)
        
        Can be called only from a script. To index pages during a user
        request, use indexPagesInNewThread.
        @arg files: iterator or list of files to index additionally
        @arg update: True = update an existing index, False = reindex everything
        """
        if not self.lock.acquire(1.0):
            self.request.log("can't index: can't acquire lock")
            return
        try:
            request = self._indexingRequest(self.request)
            self._index_pages(request, None, files, update)
        finally:
            self.lock.release()
    
    def indexPagesInNewThread(self, files=None, update=True):
        """ Index all pages in a new thread
        
        Should be called from a user request. From a script, use indexPages.
        """
        if not self.lock.acquire(1.0):
            self.request.log("can't index: can't acquire lock")
            return
        try:
            # Prevent rebuilding the index just after it was finished
            if self.exists():
                self.lock.release()
                return
            from threading import Thread
            indexThread = Thread(target=self._index_pages,
                args=(self._indexingRequest(self.request), self.lock, files, update))
            indexThread.setDaemon(True)
            
            # Join the index thread after current request finish, prevent
            # Apache CGI from killing the process.
            def joinDecorator(finish):
                def func():
                    finish()
                    indexThread.join()
                return func
                
            self.request.finish = joinDecorator(self.request.finish)        
            indexThread.start()
        except:
            self.lock.release()
            raise

    def optimize(self):
        """ Optimize the index
        
        This may take from few seconds to few hours, depending on the
        size of the wiki. Currently it's usable only from a script.
        
        TODO: needs special locking, so the index is readable until the
        optimization is finished.
        """
        if not self.exists():
            raise RuntimeError("Index does not exist or is not finished")
        if not self.lock.acquire(1.0):
            self.request.log("can't lock the index for optimization")
            return
        try:
            self._optimize(self.request)
        finally:
            self.lock.release()

    # -------------------------------------------------------------------
    # Private

    def _do_queued_updates(self, request, lock=None, amount=5):
        """ Assumes that the write lock is acquired """
        try:
            pages = self.queue.pages()[:amount]
            for name in pages:
                p = Page(request, name)
                self._update_page(p)
                self.queue.remove([name])
        finally:
            if lock:
                lock.release()

    def _update_page(self, page):
        """ Assumes that the write lock is acquired """
        reader = IndexSearcher(self.dir)
        reader.reader.deleteTerm(Term('pagename', page.page_name))
        reader.close()
        if page.exists():
            writer = IndexWriter(self.dir, False, tokenizer)
            self._index_page(writer, page, False) # we don't need to check whether it is updated
            writer.close()
   
    def contentfilter(self, filename):
        """ Get a filter for content of filename and return unicode content. """
        import mimetypes
        from MoinMoin import wikiutil
        request = self.request
        mimetype, encoding = mimetypes.guess_type(filename)
        if mimetype is None:
            mimetype = 'application/octet-stream'
        def mt2mn(mt): # mimetype to modulename
            return mt.replace("/", "_").replace("-","_").replace(".", "_")
        try:
            _filter = mt2mn(mimetype)
            execute = wikiutil.importPlugin(request.cfg, 'filter', _filter)
        except wikiutil.PluginMissingError:
            try:
                _filter = mt2mn(mimetype.split("/", 1)[0])
                execute = wikiutil.importPlugin(request.cfg, 'filter', _filter)
            except wikiutil.PluginMissingError:
                try:
                    _filter = mt2mn('application/octet-stream')
                    execute = wikiutil.importPlugin(request.cfg, 'filter', _filter)
                except wikiutil.PluginMissingError:
                    raise ImportError("Cannot load filter %s" % binaryfilter)
        try:
            data = execute(self, filename)
            request.log("Filter %s returned %d characters for file %s" % (_filter, len(data), filename))
        except (OSError, IOError), err:
            data = ''
            request.log("Filter %s threw error '%s' for file %s" % (_filter, str(err), filename))
        return data
   
    def test(self, request):
        query = BooleanQuery()
        query.add(TermQuery(Term("text", 'suchmich')), True, False)
        docs = self._search(query)
        for d in docs:
            request.log("%r %r %r" % (d, d.get('attachment'), d.get('pagename')))

    def _index_file(self, request, writer, filename, update):
        """ index a file as it were a page named pagename
            Assumes that the write lock is acquired
        """
        fs_rootpage = 'FS' # XXX FS hardcoded
        try:
            mtime = os.path.getmtime(filename)
            mtime = wikiutil.timestamp2version(mtime)
            if update:
                query = BooleanQuery()
                query.add(TermQuery(Term("pagename", fs_rootpage)), True, False)
                query.add(TermQuery(Term("attachment", filename)), True, False)
                docs = self._search(query)
                updated = len(docs) == 0 or mtime > int(docs[0].get('mtime'))
            else:
                updated = True
            request.log("%s %r" % (filename, updated))
            if updated:
                file_content = self.contentfilter(filename)
                d = document.Document()
                d.add(document.Keyword('pagename', fs_rootpage))
                d.add(document.Keyword('mtime', str(mtime)))
                d.add(document.Keyword('attachment', filename)) # XXX we should treat files like real pages, not attachments
                pagename = " ".join(os.path.join(fs_rootpage, filename).split("/"))
                d.add(document.Text('title', pagename, store=False))        
                d.add(document.Text('text', file_content, store=False))
                writer.addDocument(d)
        except (OSError, IOError), err:
            pass

    def _index_page(self, writer, page, update):
        """ Index a page - assumes that the write lock is acquired
            @arg writer: the index writer object
            @arg page: a page object
            @arg update: False = index in any case, True = index only when changed
        """
        pagename = page.page_name
        request = page.request
        mtime = page.mtime_usecs()
        if update:
            query = BooleanQuery()
            query.add(TermQuery(Term("pagename", pagename)), True, False)
            query.add(TermQuery(Term("attachment", "")), True, False)
            docs = self._search(query)
            updated = len(docs) == 0 or mtime > int(docs[0].get('mtime'))
        else:
            updated = True
        request.log("%s %r" % (pagename, updated))
        if updated:
            d = document.Document()
            d.add(document.Keyword('pagename', pagename))
            d.add(document.Keyword('mtime', str(mtime)))
            d.add(document.Keyword('attachment', '')) # this is a real page, not an attachment
            d.add(document.Text('title', pagename, store=False))        
            d.add(document.Text('text', page.get_raw_body(), store=False))
            
            links = page.getPageLinks(request)
            t = document.Text('links', '', store=False)
            t.stringVal = links
            d.add(t)
            d.add(document.Text('link_text', ' '.join(links), store=False))

            writer.addDocument(d)
        
        from MoinMoin.action import AttachFile

        attachments = AttachFile._get_files(request, pagename)
        for att in attachments:
            filename = AttachFile.getFilename(request, pagename, att)
            mtime = wikiutil.timestamp2version(os.path.getmtime(filename))
            if update:
                query = BooleanQuery()
                query.add(TermQuery(Term("pagename", pagename)), True, False)
                query.add(TermQuery(Term("attachment", att)), True, False)
                docs = self._search(query)
                updated = len(docs) == 0 or mtime > int(docs[0].get('mtime'))
            else:
                updated = True
            request.log("%s %s %r" % (pagename, att, updated))
            if updated:
                att_content = self.contentfilter(filename)
                d = document.Document()
                d.add(document.Keyword('pagename', pagename))
                d.add(document.Keyword('mtime', str(mtime)))
                d.add(document.Keyword('attachment', att)) # this is an attachment, store its filename
                d.add(document.Text('title', att, store=False)) # the filename is the "title" of an attachment
                d.add(document.Text('text', att_content, store=False))
                writer.addDocument(d)


    def _index_pages(self, request, lock=None, files=None, update=True):
        """ Index all pages (and all given files)
        
        This should be called from indexPages or indexPagesInNewThread only!
        
        This may take few minutes up to few hours, depending on the size of
        the wiki.

        When called in a new thread, lock is acquired before the call,
        and this method must release it when it finishes or fails.
        """
        try:
            self._unsign()
            start = time.time()
            writer = IndexWriter(self.dir, not update, tokenizer)
            writer.mergeFactor = 50
            pages = request.rootpage.getPageList(user='', exists=1)
            request.log("indexing all (%d) pages..." % len(pages))
            for pagename in pages:
                p = Page(request, pagename)
                # code does NOT seem to assume request.page being set any more
                #request.page = p
                self._index_page(writer, p, update)
            if files:
                request.log("indexing all files...")
                for fname in files:
                    fname = fname.strip()
                    self._index_file(request, writer, fname, update)
            writer.close()
            request.log("indexing completed successfully in %0.2f seconds." % 
                        (time.time() - start))
            self._optimize(request)
            self._sign()
        finally:
            if lock:
                lock.release()

    def _optimize(self, request):
        """ Optimize the index """
        self._unsign()
        start = time.time()
        request.log("optimizing index...")
        writer = IndexWriter(self.dir, False, tokenizer)
        writer.optimize()
        writer.close()
        request.log("optimizing completed successfully in %0.2f seconds." % 
                    (time.time() - start))
        self._sign()

    def _indexingRequest(self, request):
        """ Return a new request that can be used for index building.
        
        This request uses a security policy that lets the current user
        read any page. Without this policy some pages will not render,
        which will create broken pagelinks index.        
        """
        from MoinMoin.request import RequestCLI
        from MoinMoin.security import Permissions        
        request = RequestCLI(request.url)
        class SecurityPolicy(Permissions):            
            def read(*args, **kw):
                return True        
        request.user.may = SecurityPolicy(request.user)
        return request

    def _unsign(self):
        """ Remove sig file - assume write lock acquired """
        try:
            os.remove(self.sig_file)
        except OSError, err:
            if err.errno != errno.ENOENT:
                raise

    def _sign(self):
        """ Add sig file - assume write lock acquired """
        f = file(self.sig_file, 'w')
        try:
            f.write('')
        finally:
            f.close()

