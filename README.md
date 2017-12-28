# Module and tools for managing old Alcatel AOS devices
SSH server implementation in old versions of AOS (v6.4.4 and earlier) supports only single ssh channel per session.
Remote command execution requests are constantly failing with error:
```
$ ssh <some deivce> <some command>
<user>@<some device>'s password: 
exec request failed on channel 0
```

This project provides modules and tools to manage old Alcatel AOS devices via single SSH channel. 

## Module usage
Module usage is pretty simple.

Code:
```python
import alcatel
import json

host = 'hostname'  # or ip address 
username = 'username'
password = 'password'
command = 'show ip interface'

switch = alcatel.connect(host, username, password, port=22)
raw_output = switch.send_command(command)
parsed_output = alcatel.parse(command, raw_output)

print('--- raw_output:')
print(raw_output)
print('--- parsed_output:')
print(json.dumps(parsed_output, sort_keys=True, indent=4))
print('---')
```
Output:
```
--- raw_output:
Total 3 interfaces
        Name            IP Address     Subnet Mask   Status Forward  Device
--------------------+---------------+---------------+------+-------+----------------------------------------------------
Loopback             127.0.0.1       255.0.0.0           UP      NO Loopback
net1                 192.168.1.1     255.255.255.0       UP     YES vlan 1  
net2                 192.168.2.1     255.255.255.0       UP     YES vlan 2
--- parsed_output:
[
    {
        "device": "Loopback",
        "forward": "NO",
        "ip_address": "127.0.0.1",
        "mask": "255.0.0.0",
        "name": "Loopback",
        "status": "UP"
    },
    {
        "device": "vlan 1",
        "forward": "YES",
        "ip_address": "192.168.1.1",
        "mask": "255.255.255.0",
        "name": "net1",
        "status": "UP"
    },
    {
        "device": "vlan 2",
        "forward": "YES",
        "ip_address": "192.168.2.1",
        "mask": "255.255.255.0",
        "name": "net2",
        "status": "UP"
    }
]
---
```
### alcatel-ssh tool usage
```
usage: alcatel-ssh [-h] [-u username] [-p password] [-P port] [-j] [-v] [-t]
                   host command [command ...]

Remote command execution over ssh on Alcatel AOS devices (v6.4.4 and earlier).

positional arguments:
  host                  host name or ip address to connect
  command               command to execute

optional arguments:
  -h, --help            show this help message and exit
  -u username, --username username
                        use username (could be taken from ALCATEL_USER env
                        var)
  -p password, --password password
                        use password (could be taken from ALCATEL_PASS env
                        var)
  -P port, --port port  connect to non-default port
  -j, --json            return json output
  -v, --verbose         print additional information to stderr
  -t, --traceback       print python traceback for error debugging

alcatel-ssh v0.1
```
## Installation
### Linux (and probably MacOS)
1. git clone https://github.com/artgromov/alcatel_aos
2. cd alcatel_aos
3. pip3 install -r requirements.txt
4. chmod a+x bin/alcatel-ssh.py
5. create softlink for bin/alcatel-ssh.py to any directory from your PATH
6. create softlink for lib/alcatel to any directory from your PYTHONPATH
