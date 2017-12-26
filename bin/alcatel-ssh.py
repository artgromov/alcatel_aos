#!/usr/bin/env python3
import argparse
import logging
import socket
import sys
import alcatel
import json
import getpass
from paramiko.ssh_exception import SSHException, AuthenticationException


logger = logging.getLogger('alcatel-ssh')
logging.getLogger().setLevel(logging.CRITICAL)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Remote command execution over ssh on legacy Alcatel OmniSwitch.',
                                     epilog='alcatel-ssh %s' % alcatel.__version_string__)

    parser.add_argument('-v', '--verbose',
                        action='count',
                        default=0,
                        help='print debugging infromation to stderr')

    parser.add_argument('-d', '--debug',
                        action='store_true',
                        help='raise python exceptions for debugging')

    parser.add_argument('-j', '--json',
                        action='store_true',
                        help='return json output')

    parser.add_argument('-u', '--username',
                        metavar='username',
                        help='specify username',
                        default=None)

    parser.add_argument('-p', '--password',
                        metavar='password',
                        help='specify password',
                        default=None)

    parser.add_argument('-P', '--port',
                        metavar='port',
                        help='specify ssh port',
                        type=int,
                        default=22)

    parser.add_argument('-e', '--expect',
                        metavar='expect',
                        help='string to expect',
                        default=None)

    parser.add_argument('host',
                        metavar='host',
                        help='host name or ip address to connect to')

    parser.add_argument('command',
                        metavar='command',
                        nargs='+',
                        help='command to execute')

    args = parser.parse_args()

    if args.verbose == 0:
        logging_level = logging.WARNING
        logging_format = '%(message)s'
    if args.verbose >= 1:
        logging_level = logging.INFO
        logging_format = '%(levelname)s - %(message)s'
    if args.verbose >= 2:
        logging_level = logging.DEBUG
        logging_format = '%(name)s - %(levelname)s - %(message)s'
    if args.verbose >= 5:
        logging_level = 5
        logging_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    logging.basicConfig(format=logging_format)
    for logger_name in ['alcatel-ssh', 'alcatel.alcatel_legacy_os']:
        logging.getLogger(logger_name).setLevel(logging_level)

    logger.debug('parsed args: %s' % args)

    try:
        username = args.username
        if username is None:
            username = getpass.getuser()
            if username is None or username == '':
                username = input('Enter username: ')
                if username == '':
                    logger.error('Username cannot be empty')
                    sys.exit(1)

        password = args.password
        if password is None:
            password = getpass.getpass('Enter password: ')
            if password == '':
                logger.error('Password cannot be empty')
                sys.exit(1)

        host = socket.gethostbyname(args.host)

        command = ' '.join(args.command)

        switch = alcatel.connect(host, username, password)
        output = switch.send_command(command, expect=args.expect)

        if args.json:
            json_output = {
                'command': command,
                'output': output,
                'output_lines': output.split('\n'),
            }
            print(json.dumps(json_output, sort_keys=True, indent=4))

        else:
            print(output)

    except AuthenticationException:
        logger.error('Authentication failed.')
        sys.exit(1)

    except KeyboardInterrupt:
        logger.error('Exiting by keyboard interrupt.')
        sys.exit(1)

    except socket.gaierror:
        logger.error('Name or service not known or incorrect ip address.')
        sys.exit(2)

    except SSHException as e:
        if args.debug:
            raise
        else:
            if e.args[0] == 'Error reading SSH protocol banner':
                logger.error('SSH legacy OmniSwitch error. Please wait for 2-5 minutes.')
                sys.exit(5)
            else:
                logger.error('SSH error: %s' % e.args[0].lower())
                sys.exit(4)

    except Exception as e:
        if args.debug:
            raise
        else:
            logger.error('Unexpected error: %s.' % e.args[0])
            sys.exit(9)
