import os
import pdb
import smtplib
import socket
import sys
from email.mime.text import MIMEText
from importlib import import_module
from textwrap import dedent
from urlparse import urlparse

from cfme.exceptions import TemplateNotFound
from fixtures.pytest_store import write_line
from utils import conf
from utils.log import logger

_breakpoint_exceptions = {}

# defaults
smtp_conf = {
    'server': 'localhost'
}
# Update defaults from conf
smtp_conf.update(conf.env.get('smtp', {}))


for breakpoint in conf.rdb['breakpoints']:
    for i, exc_name in enumerate(breakpoint['exceptions']):
        split_exc = exc_name.rsplit('.', 1)
        exc = getattr(import_module(split_exc[0]), split_exc[1])
        # stash exceptions for easy matching in exception handlers
        _breakpoint_exceptions[exc] = breakpoint


def pytest_exception_interact(node, call, report):
    if type(call.excinfo.value) not in _breakpoint_exceptions:
        return
    else:
        breakpoint = _breakpoint_exceptions[exc]

    rdb = Rdb()
    host, port = rdb.sock.getsockname()
    # Try to guess a hostname based on jenkins env, otherwise just list the port
    if os.environ.get('JENKINS_URL'):
        parsed = urlparse(os.environ['JENKINS_URL'])
        endpoint = 'host {} port {}'.format(parsed.hostname, port)
    else:
        endpoint = 'pytest runner port {}'.format(port)
    subject = 'RDB Breakpoint: {}'.format(breakpoint['subject'])
    body = dedent("""\
    A py.test run encountered an error. The remote debugger is running
    on {} (TCP), waiting for telnet connection.
    """).format(endpoint)
    smtp = smtplib.SMTP(smtp_conf['server'])
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['To'] = ', '.join(breakpoint['recipients'])
    smtp.sendmail('cloudforms-qe@redhat.com', breakpoint['recipients'], msg.as_string())
    rdb.set_trace()


class Rdb(pdb.Pdb):
    def __init__(self):
        self.old_stdout = sys.stdout
        self.old_stdin = sys.stdin
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # bind to random port
        self.sock.bind(('0.0.0.0', 0))

    def do_continue(self, arg):
        sys.stdout = self.old_stdout
        sys.stdin = self.old_stdin
        self.sock.close()
        self.set_continue()
        return 1
    do_c = do_cont = do_continue

    def set_trace(self, *args, **kwargs):
        host, port = self.sock.getsockname()
        msg = 'Remote debugger listening on TCP {}'.format(port)
        logger.error(msg)
        write_line(msg)
        self.sock.listen(1)
        (clientsocket, address) = self.sock.accept()
        handle = clientsocket.makefile('rw')
        pdb.Pdb.__init__(self, completekey='tab', stdin=handle, stdout=handle)
        sys.stdout = sys.stdin = handle
        pdb.Pdb.set_trace(self, *args, **kwargs)


def test_rdb():
    raise TemplateNotFound
