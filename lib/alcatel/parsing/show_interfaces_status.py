def post_parse(data):
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

    new_data = []

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

        new_data.append(new_entry)

    return new_data
