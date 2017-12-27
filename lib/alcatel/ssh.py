import paramiko
from datetime import datetime, timedelta
import socket
import logging
import textfsm
from threading import RLock
import os

from alcatel.parsing import parse

logger = logging.getLogger(__name__)


DSA_PATCHED = False


def patch_dsa():
    """this is nesessary to make paramiko and cryptography work with legacy OmniSwitch devices"""
    global DSA_PATCHED
    if not DSA_PATCHED:
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

        DSA_PATCHED = True


class AlcatelSSH:
    def __init__(self, ip, username, password, port=22, *, connection_timeout=5, keepalive=5,
                 missing_host_key_policy=paramiko.client.AutoAddPolicy()):
        patch_dsa()

        self.ip = ip
        self.username = username
        self.password = password
        self.port = port

        self.connection_timeout = connection_timeout
        self.keepalive = keepalive
        self.missing_host_key_policy = missing_host_key_policy

        self.encoding = os.getenv('LANG')
        if self.encoding is None:
            self.encoding = 'utf-8'  # TODO: find out better way to define encoding
        else:
            self.encoding = self.encoding.lower().split('.')[1]
        logger.debug('encoding: %s' % self.encoding)

        self.ssh = None

        self.thread_lock = RLock()

    def _connect(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(self.missing_host_key_policy)
        logger.info('connecting to %s:%s' % (self.ip, self.port))
        self.ssh.connect(
            hostname=self.ip,
            username=self.username,
            password=self.password,
            port=self.port,
            timeout=self.connection_timeout,
            allow_agent=False,
        )

        self.transport = self.ssh.get_transport()
        self.transport.set_keepalive(self.keepalive)
        self.channel = self.ssh.invoke_shell(width=0, height=0)

        recv_buffer = b''
        recv_end = None
        while True:
            if self.channel.recv_ready():
                logger.log(5, '_connect recv_buffer: {}'.format(recv_buffer))
                recv_end = datetime.now() + timedelta(seconds=1)
                data = self.channel.recv(1024)
                recv_buffer += data
            elif recv_end is not None and datetime.now() > recv_end:
                break

        self.prompt = recv_buffer.decode(self.encoding).replace('\r\n', '\n').split('\n')[-1]
        logger.debug('prompt: %s' % self.prompt)

    def _ensure_connected(self):
        if self.ssh is None:
            self._connect()

        if self.channel.closed:
            logger.debug('reconnecting, channel closed')
            self._connect()

    def _send(self, command):  # TODO: test with big send_buffer
        self._ensure_connected()

        if isinstance(command, list) or isinstance(command, tuple):
            send_string = '\n'.join(command)
        else:
            send_string = str(command)

        send_string = send_string + '\n'
        send_buffer = bytes(send_string, encoding=self.encoding)
        return self.channel.send(send_buffer)

    def _recv(self, expect, timeout):
        self._ensure_connected()

        if expect is None:
            expect = self.prompt.encode(self.encoding)
        else:
            expect = expect.encode(self.encoding)

        recv_timeout = datetime.now() + timedelta(seconds=timeout)
        recv_buffer = b''
        while True:
            data = self.channel.recv(1024)
            recv_buffer += data
            logger.log(5, 'recv_buffer: %s' % recv_buffer)
            if recv_buffer.endswith(expect) or datetime.now() > recv_timeout:
                break

        recv_string = recv_buffer.decode(self.encoding)
        return recv_string

    def _recv_parse(self, output, command):
        # TODO: test line endings processing on multiple platforms
        output = output.lstrip(command)\
                       .lstrip('\r\n')\
                       .rstrip(self.prompt)\
                       .rstrip('\r\n')

        output_lines = output.split('\r\n')

        status = 'ok'
        for line in output_lines:
            if line.startswith('ERROR: '):
                status = 'error'
                break

        output_data = None
        if status == 'ok':
            output_data = parse(command, output)

        result = {
            'parser_key': command,
            'status': status,
            'output': output,
            'output_lines': output_lines,
            'output_data': output_data,
        }

        return result

    def send_command(self, command, *, expect=None, timeout=10):
        with self.thread_lock:
            self._send(command)
            recv_string = self._recv(expect, timeout)
            result = self._recv_parse(recv_string, command)
            return result

    def send_command_set(self, command_list):
        with self.thread_lock:
            result_list = []
            for command in command_list:
                result = self.send_command(command)
                result_list.append(result)
            return result_list

    def close(self):
        self.transport.close()






