import os
import logging
import textfsm
from functools import partial
from importlib import import_module


logger = logging.getLogger(__name__)


PARSINGDIR = os.path.dirname(os.path.realpath(__file__))


def parse_textfsm(template_name, output):
    logger.debug('parsing using template file: %s' % template_name)
    filename = os.path.join(PARSINGDIR, template_name)
    with open(filename) as file:
        template = textfsm.TextFSM(file)
    keys = template.header
    values = template.ParseText(output)
    data = []
    for line in values:
        entry = dict()
        for key_num, value in enumerate(line):
            key = keys[key_num]
            entry[key] = value
        data.append(entry)
    return data


def parse(command, output):
    func = None
    parser_key = command.replace(' ', '_').replace('-', '_')
    logger.debug('lookup with parser_key: %s' % parser_key)
    for filename in sorted(os.listdir(PARSINGDIR)):
        name, ext = os.path.splitext(filename)

        if parser_key == name:
            if ext == '.py':
                module_name = 'alcatel.parsing.%s' % name
                logger.debug('found module: %s' % module_name)
                func = import_module(module_name).parse

            elif ext == '.template' and func is None:
                template_name = filename
                logger.debug('found template: %s' % template_name)
                func = partial(parse_textfsm, template_name)

    if func is None:
        logger.debug('nothing found, returning None')
        return None
    else:
        return func(output)

