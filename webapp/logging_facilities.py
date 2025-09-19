from collections import defaultdict
from logging import config, handlers
import logging
import threading

class SMTP_SSLHandler(logging.Handler):
    def __init__(self, mailhost, fromaddr, toaddrs, subject, credentials):
        """
        This is basically a copy of logging.handlers.SMTPHandler
        """
        logging.Handler.__init__(self)
        if isinstance(mailhost, tuple):
            self.mailhost, self.mailport = mailhost
        else:
            self.mailhost, self.mailport = mailhost, None
        self.username, self.password = credentials
        self.fromaddr = fromaddr
        if isinstance(toaddrs, basestring):
            toaddrs = [toaddrs]
        self.toaddrs = toaddrs
        self.subject = subject

    def getSubject(self, record):
        """
        Determine the subject for the email.

        If you want to specify a subject line which is record-dependent,
        override this method.
        """
        return self.subject

    def emit(self, record):
        """
        Emit a record.

        Format the record and send it to the specified addressees.
        """
        try:
            import smtplib
            from email.utils import formatdate
            port = self.mailport
            if not port:
                port = smtplib.SMTP_SSL_PORT
            smtp = smtplib.SMTP_SSL(self.mailhost, port)
            msg = self.format(record)
            msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\nDate: %s\r\n\r\n%s" % (
                            self.fromaddr,
                            ",".join(self.toaddrs),
                            self.getSubject(record),
                            formatdate(), msg)
            
            smtp.login(self.username, self.password)
            smtp.sendmail(self.fromaddr, self.toaddrs, msg.encode('utf-8'))
            smtp.quit()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
            
class ContextAwareFormatter(logging.Formatter):
    """
    Makes use of get_context() to populate the record attributes.
    """

    def format(self, record):
        # Using defaultdict to avoid KeyErrorS when a key is not in the context.
        def factory():
            return ""
        record.__dict__ = defaultdict(factory, record.__dict__)

        for k, v in get_context().iteritems():
            if not hasattr(record, k):
                setattr(record, k, v)
                
        return logging.Formatter.format(self, record)
    


THREADLOCAL_ATTR = "logging_context"
_threadlocal = threading.local()

def get_context():
    result = getattr(_threadlocal, THREADLOCAL_ATTR, None)
    if result is None:
        result = {}
        setattr(_threadlocal, THREADLOCAL_ATTR, result)
    return result

def set_context(**context):
    c = get_context()
    c.clear()
    c.update(**context)
    return c

def update_context(**context):
    c = get_context()
    c.update(**context)
    return c