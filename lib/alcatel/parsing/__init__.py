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
    default_parse_stack = {
        'pre_parse': lambda data: data,
        'parse': lambda data: data,
        'post_parse': lambda data: data,
    }

    parse_stack = {}

    parser_key = command.replace(' ', '_').replace('-', '_')
    logger.debug('lookup parser functions with parser_key: %s' % parser_key)

    modules = [i.rstrip('.py') for i in os.listdir(PARSINGDIR) if i.endswith('.py') and i != os.path.basename(__file__)]
    templates = [i.rstrip('.template') for i in os.listdir(PARSINGDIR) if i.endswith('.template')]

    if parser_key in modules:
        module_name = 'alcatel.parsing.%s' % parser_key
        module_obj = import_module(module_name)

        for stage in ['pre_parse', 'parse', 'post_parse']:
            try:
                stage_func = getattr(module_obj, stage)
                logger.debug('using %s function from module: %s' % (stage, module_name))
            except AttributeError:
                if stage == 'parse' and parser_key in templates:
                    template_name = parser_key + '.template'
                    logger.debug('using template_parse function')
                    parse_stack['parse'] = partial(template_parse, template_name)
                    continue
                stage_func = default_parse_stack[stage]
                logger.debug('using default_%s function' % stage)

            parse_stack[stage] = stage_func

    output_data = input_data
    for stage in ['pre_parse', 'parse', 'post_parse']:
        logger.debug('running stage: %s' % stage)
        func = parse_stack[stage]
        output_data = func(output_data)

    if output_data == input_data:
        return None
    else:
        return output_data
