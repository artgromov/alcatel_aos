#!/usr/bin/env python3
import argparse
import logging
import os
import sys
import traceback
import socket
import alcatel
import json
import getpass
from paramiko.ssh_exception import *


logger = logging.getLogger('alcatel-ssh')
logging.getLogger('paramiko.transport').setLevel(logging.CRITICAL)


class InputException(Exception):
    pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Remote command execution over ssh on legacy Alcatel OmniSwitch.',
                                     epilog='alcatel-ssh %s' % alcatel.__version_string__)
    # TODO: add -f option to read command lines from file
    # TODO: add -i option to read from stdin (may require to make <command> arg optional?)
    parser.add_argument('-u', '--username',
                        metavar='username',
                        help='Specify username. Could be set in USER env var.',
                        default=None)

    parser.add_argument('-p', '--password',
                        metavar='password',
                        help='Specify password. Could be set in PASS env var.',
                        default=None)

    parser.add_argument('-P', '--port',
                        metavar='port',
                        help='Specify ssh port.',
                        type=int,
                        default=22)

    parser.add_argument('-j', '--json',
                        action='store_true',
                        help='Return json output.')

    parser.add_argument('-v', '--verbose',
                        action='count',
                        default=0,
                        help='Print additional infromation to stderr.')

    parser.add_argument('-t', '--traceback',
                        action='store_true',
                        help='Print python traceback for debugging.')

    parser.add_argument('host',
                        metavar='host',
                        help='Host name or ip address to connect to.')

    parser.add_argument('command',
                        metavar='command',
                        nargs='+',
                        help='Command to execute.')

    args = parser.parse_args()

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

    logging.basicConfig(format=logging_format, level=logging_level)

    logger.debug('parsed args: %s' % args)

    try:
        try:
            # nested try for traceback printing

            username = args.username
            if username is None:
                username = os.environ.get('ALCATEL_USER', None)
                if username is None or username == '':
                    username = input('Enter username: ')
                    if username == '':
                        raise InputException('Username cannot be empty.')

            password = args.password
            if password is None:
                password = os.environ.get('ALCATEL_PASS', None)
                if password is None or password == '':
                    password = getpass.getpass('Enter password: ')
                    if password == '':
                        raise InputException('Password cannot be empty.')

            host = socket.gethostbyname(args.host)

            command = ' '.join(args.command)

            switch = alcatel.connect(host, username, password, port=args.port)

            output = switch.send_command(command)

            if args.json:
                json_output = {
                    'command': command,
                    'output': output,
                    'output_lines': output.split('\n'),
                }
                print(json.dumps(json_output, sort_keys=True, indent=4))

            else:
                print(output)

        except Exception as e:
            if args.traceback:
                traceback.print_exc()
            raise

    except KeyboardInterrupt:
        logger.error('Exiting by keyboard interrupt.')
        sys.exit(0)

    except InputException as e:
        logger.error(e.args[0])
        sys.exit(1)  # User input errors

    except socket.error as e:
        logger.error('Socket error: %s.' % e.args[1])
        sys.exit(2)

    except AuthenticationException as e:
        logger.error('Authentication error: %s.' % e.args[0])
        sys.exit(3)

    except SSHException as e:
        if e.args[0] == 'Error reading SSH protocol banner':
            logger.error('SSH legacy OmniSwitch error. Please wait for 2-5 minutes.')
            sys.exit(5)  # Special case

        logger.error('SSH error: %s.' % e.args[0])
        sys.exit(4)

    except Exception as e:
        logger.error('Unexpected error: %s.' % e.args[0])
        sys.exit(9)
