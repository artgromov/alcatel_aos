import os


__version__ = (0, 1)
__version_string__ = 'v' + '.'.join(str(i) for i in __version__)


PROJECTDIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
LIBDIR = os.path.join(PROJECTDIR, 'lib')
BINDIR = os.path.join(PROJECTDIR, 'bin')
ETCDIR = os.path.join(PROJECTDIR, 'etc')


from alcatel.legacy_ssh import AlcatelLegacySSH


def connect(host, username, password, port):
    switch = AlcatelLegacySSH(host, username, password, port)
    return switch
