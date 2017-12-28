import os
import logging
import textfsm
from functools import partial
from importlib import import_module


logger = logging.getLogger(__name__)


PARSINGDIR = os.path.dirname(os.path.realpath(__file__))


def template_parse(template_name, output):
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


def parse(command, input_data):
    parser_key = command.replace(' ', '_').replace('-', '_')
    logger.debug('lookup parser functions with parser_key: %s' % parser_key)

    files = os.listdir(PARSINGDIR)

    modules = [i[:-3] for i in files if i.endswith('.py') and i != os.path.basename(__file__)]
    logger.debug('available modules: %s' % modules)
    module = None
    if parser_key in modules:
        module = 'alcatel.parsing.%s' % parser_key
        module_obj = import_module(module)
        logger.debug('found module: %s' % module)

    templates = [i[:-9] for i in files if i.endswith('.template')]
    logger.debug('available templates: %s' % templates)
    template = None
    if parser_key in templates:
        template = parser_key + '.template'
        logger.debug('found template: %s' % template)

    parse_stack = {}
    for stage in ['pre_parse', 'parse', 'post_parse']:
        if module:
            try:
                parse_stack[stage] = getattr(module_obj, stage)
                logger.info('using %s function from module: %s' % (stage, module))
                continue
            except AttributeError:
                pass

        if stage == 'parse' and template:
            parse_stack[stage] = partial(template_parse, template)
            logger.info('using template_parse function with template: %s' % template)
            continue

        parse_stack[stage] = lambda data: data
        logger.info('using default_%s function' % stage)

    output_data = input_data
    for stage in ['pre_parse', 'parse', 'post_parse']:
        logger.debug('running stage: %s' % stage)
        func = parse_stack[stage]
        output_data = func(output_data)

    if output_data == input_data:
        return None
    else:
        return output_data
