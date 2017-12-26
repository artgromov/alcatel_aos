import paramiko
from datetime import datetime, timedelta
import socket
import logging
from threading import RLock
import os


logger = logging.getLogger(__name__)


class AlcatelLegacyOmniSwitch:
    def __init__(self, ip, username, password, port=22, *, connection_timeout=5, keepalive=5,
                 missing_host_key_policy=paramiko.client.AutoAddPolicy()):

        self.ip = ip
        self.username = username
        self.password = password
        self.port = port

        self.connection_timeout = connection_timeout
        self.keepalive = keepalive
        self.missing_host_key_policy = missing_host_key_policy

        self.encoding = os.getenv('LANG')
        if self.encoding is None:
            self.encoding = 'utf-8'
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

    def _send(self, command):
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

    def _recv_clean(self, recv_string, command):
        recv_string = recv_string.replace('\r\n', '\n')
        recv_string = recv_string.lstrip(command)
        recv_string = recv_string.rstrip(self.prompt)
        recv_string = recv_string.strip()
        return recv_string

    def send_command(self, command, *, expect=None, timeout=10):
        with self.thread_lock:
            self._send(command)
            raw_output = self._recv(expect, timeout)
            output = self._recv_clean(raw_output, command)
            return output

    def send_command_set(self, command_list):
        with self.thread_lock:
            output_list = []
            for command in command_list:
                output = self.send_command(command)
                output_list.append(output)

            return output_list

    def close(self):
        self.transport.close()






