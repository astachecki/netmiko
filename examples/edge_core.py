from netmiko import ConnectHandler

edge_core = {
    'device_type': 'edgecore',
    'ip':   '192.168.0.20',
    'username': 'admin',
    'password': 'admin',
    'port': 22,          # optional, defaults to 22
    'verbose': True,       # optional, defaults to False
    'kex_cipher': 'diffie-hellman-group1-sha1',
    'key_cipher': 'ssh-dss',
    'allow_agent': False,
    'use_keys': False,
    'timeout': 20,
}

net_connect = ConnectHandler(**edge_core)

print net_connect.send_command(
    'show interfaces status',
    page_string='---More---',
)
