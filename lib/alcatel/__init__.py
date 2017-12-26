__version__ = (0, 1)
__version_string__ = 'v' + '.'.join(str(i) for i in __version__)


from alcatel.legacy_ssh import AlcatelLegacySSH


def connect(host, username, password):
    switch = AlcatelLegacySSH(host, username, password)
    return switch
