# -*- coding: iso-8859-1 -*-
"""
    MoinMoin - email helper functions

    @copyright: 2003 by J�rgen Hermann <jh@web.de>
    @license: GNU GPL, see COPYING for details.
"""

import os, re
from email.Header import Header
from MoinMoin import config

_transdict = {"AT": "@", "DOT": ".", "DASH": "-"}


def encodeAddress(address, charset):
    """ Encode email address to enable non ascii names 
    
    e.g. '"J�rgen Hermann" <jh@web.de>'. According to the RFC, the name
    part should be encoded, the address should not.
    
    @param address: email address, posibly using '"name" <address>' format
    @type address: unicode
    @param charset: sepcifying both the charset and the encoding, e.g
        quoted printble or base64.
    @type charset: email.Charset.Charset instance
    @rtype: string
    @return: encoded address
    """   
    composite = re.compile(r'(?P<phrase>.+)(?P<angle_addr>\<.*\>)', 
                           re.UNICODE)
    match = composite.match(address)
    if match:
        phrase = match.group('phrase').encode(config.charset)
        phrase = str(Header(phrase, charset))
        angle_addr = match.group('angle_addr').encode(config.charset)       
        return phrase + angle_addr
    else:
        return address.encode(config.charset)


def sendmail(request, to, subject, text, **kw):
    """ Create and send a text/plain message
        
    Return a tuple of success or error indicator and message.
    
    @param request: the request object
    @param to: recipients (list)
    @param subject: subject of email (unicode)
    @param text: email body text (unicode)
    @keyword mail_from: override default mail_from
    @type mail_from: unicode
    @rtype: tuple
    @return: (is_ok, Description of error or OK message)
    """
    import smtplib, socket
    from email.Message import Message
    from email.Charset import Charset, QP
    from email.Utils import formatdate, make_msgid

    _ = request.getText
    cfg = request.cfg    
    mail_from = kw.get('mail_from', '') or cfg.mail_from
    subject = subject.encode(config.charset)    

    # Create a text/plain body using CRLF (see RFC2822)
    text = text.replace(u'\n', u'\r\n')
    text = text.encode(config.charset)

    # Create a message using config.charset and quoted printable
    # encoding, which should be supported better by mail clients.
    # TODO: check if its really works better for major mail clients
    msg = Message()
    charset = Charset(config.charset)
    charset.header_encoding = QP
    charset.body_encoding = QP
    msg.set_charset(charset)    
    msg.set_payload(charset.body_encode(text))
    
    # Create message headers
    # Don't expose emails addreses of the other subscribers, instead we
    # use the same mail_from, e.g. u"J�rgen Wiki <noreply@mywiki.org>"
    address = encodeAddress(mail_from, charset) 
    msg['From'] = address
    msg['To'] = address
    msg['Date'] = formatdate()
    msg['Message-ID'] = make_msgid()
    msg['Subject'] = Header(subject, charset)
    
    if cfg.mail_sendmail:
        # Set the BCC.  This will be stripped later by sendmail.
        msg['BCC'] = ','.join(to)
        # Set Return-Path so that it isn't set (generally incorrectly) for us.
        msg['Return-Path'] = address

    # Send the message
    if not cfg.mail_sendmail:
        try:
            host, port = (cfg.mail_smarthost + ':25').split(':')[:2]
            server = smtplib.SMTP(host, int(port))
            try:
                #server.set_debuglevel(1)
                if cfg.mail_login:
                    user, pwd = cfg.mail_login.split()
                    try: # try to do tls
                        server.ehlo()
                        if server.has_extn('starttls'):
                            server.starttls()
                            server.ehlo()
                    except:
                        pass
                    server.login(user, pwd)
                server.sendmail(mail_from, to, msg.as_string())
            finally:
                try:
                    server.quit()
                except AttributeError:
                    # in case the connection failed, SMTP has no "sock" attribute
                    pass
        except smtplib.SMTPException, e:
            return (0, str(e))
        except (os.error, socket.error), e:
            return (0, _("Connection to mailserver '%(server)s' failed: %(reason)s") % {
                'server': cfg.mail_smarthost, 
                'reason': str(e)
            })
    else:
        try:
            sendmailp = os.popen(cfg.mail_sendmail, "w") 
            # msg contains everything we need, so this is a simple write
            sendmailp.write(msg.as_string())
            sendmail_status = sendmailp.close()
            if sendmail_status:
                return (0, str(sendmail_status))
        except:
            return (0, _("Mail not sent"))

    return (1, _("Mail sent OK"))


def decodeSpamSafeEmail(address):
    """ Decode obfuscated email address to standard email address

    Decode a spam-safe email address in `address` by applying the
    following rules:
    
    Known all-uppercase words and their translation:
        "DOT"   -> "."
        "AT"    -> "@"
        "DASH"  -> "-"

    Any unknown all-uppercase words simply get stripped.
    Use that to make it even harder for spam bots!

    Blanks (spaces) simply get stripped.
    
    @param address: obfuscated email address string
    @rtype: string
    @return: decoded email address
    """
    email = []

    # words are separated by blanks
    for word in address.split():
        # is it all-uppercase?
        if word.isalpha() and word == word.upper():
            # strip unknown CAPS words
            word = _transdict.get(word, '')
        email.append(word)

    # return concatenated parts
    return ''.join(email)

