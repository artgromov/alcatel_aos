__version__ = (0, 1)
__version_string__ = 'v' + '.'.join(str(i) for i in __version__)


# this is nesessary to make paramiko and cryptography work with legacy OmniSwitch devices
from cryptography import utils
from cryptography.hazmat.primitives.asymmetric import dsa

def _override_check_dsa_parameters(parameters):
    if utils.bit_length(parameters.p) not in [512, 1024, 2048, 3072]:
        raise ValueError("p must be exactly 512, 1024, 2048, or 3072 bits long")
    if utils.bit_length(parameters.q) not in [160, 256]:
        raise ValueError("q must be exactly 160 or 256 bits long")
    if not (1 < parameters.g < parameters.p):
        raise ValueError("g, p don't satisfy 1 < g < p.")

dsa._check_dsa_parameters = _override_check_dsa_parameters


from alcatel.alcatel_legacy_os import AlcatelLegacyOmniSwitch


def connect(host, username, password):
    switch = AlcatelLegacyOmniSwitch(host, username, password)
    return switch
