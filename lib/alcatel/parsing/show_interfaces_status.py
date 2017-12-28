import os
import logging
from alcatel.parsing import parse_textfsm


logger = logging.getLogger(__name__)


def parse(output):
    template_name = os.path.basename(__file__).rstrip('.py') + '.template'
    data = parse_textfsm(template_name, output)

    hybrid_modes = {
        'FF': 'ForcedFiber',
        'FC': 'ForcedCopper',
        'PF': 'PreferredFiber',
        'PC': 'PreferredCopper',
        'F': 'Fiber',
        'C': 'Copper',
        'NA': None,
        '-': None,
    }

    with_types = []

    for entry in data:
        new_entry = dict()
        for key, value in entry.items():
            if key in ('slot', 'port', 'configured_speed_mbps'):
                if value == '-':
                    new_entry[key] = None
                else:
                    try:
                        new_entry[key] = int(value)
                    except ValueError:
                        new_entry[key] = value.lower()

            if key in ('autonegotiation', 'trap_linkupdown'):
                if value == '-':
                    new_entry[key] = False
                else:
                    new_entry[key] = True

            if key == 'detected_speed_mbps':
                if value == '-':
                    new_entry[key] = None
                    new_entry['connected'] = False
                else:
                    new_entry[key] = int(value)
                    new_entry['connected'] = True

            if key in ('detected_duplex', 'configured_duplex'):
                if value == '-':
                    new_entry[key] = None
                else:
                    new_entry[key] = value.lower()

            if key in ('detected_hybrid_mode', 'configured_hybrid_mode'):
                try:
                    new_entry[key] = hybrid_modes[value]
                except KeyError:
                    new_entry[key] = value

        with_types.append(new_entry)

    # TODO: remote duplicate interfaces (pick preferred or active one from hybrid interface pair)
    # duplicate_pairs = set()
    # duplicate_indices = set()
    # indices = list(range(len(with_types)))
    # for i in indices:
    #     for j in indices[i+1:]:
    #         a = with_types[i]
    #         b = with_types[j]
    #         if a['slot'] == b['slot'] and a['port'] == b['port']:
    #             duplicate_pairs.add(tuple(sorted([i, j])))
    #             duplicate_indices.add(i)
    #             duplicate_indices.add(j)
    #
    # logger.debug('duplicate pairs found: %s' % duplicate_pairs)
    #
    # without_duplicates = []
    # for i, entry in enumerate(with_types):
    #     if i not in duplicate_indices:
    #         without_duplicates.append(entry)
    #     else:
    #         if entry['connected']:
    #             without_duplicates.append(entry)
    #         else:
    #             for pair in duplicate_pairs:
    #                 if i in pair:
    #                     pair_list = list(pair)
    #                     pair_list.remove(i)
    #                     j = pair_list[0]
    #                     without_duplicates.append(with_types[j])

    return with_types
