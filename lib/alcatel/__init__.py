import os
__version__ = (0, 1)
__version_string__ = 'v' + '.'.join(str(i) for i in __version__)


PROJECTDIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
LIBDIR = os.path.join(PROJECTDIR, 'lib')
BINDIR = os.path.join(PROJECTDIR, 'bin')
ETCDIR = os.path.join(PROJECTDIR, 'etc')


from alcatel.ssh import AlcatelSSH
from alcatel.parsing import PARSINGDIR, parse


session_cache = dict()


def connect(ip, username, password, port):
    key = '{}_{}_{}'.format(ip, port, username)
    try:
        switch = session_cache[key]
    except KeyError:
        switch = AlcatelSSH(ip, username, password, port)
        session_cache[key] = switch

    return switch
