# Configuration and State Management

import socket

# Ports
MULTICAST_PORT = 10000
SERVER_PORT = 10001

# Hosts
BUFFER_SIZE = 1024
UNICODE = 'utf-8'
MULTICAST_IP = '224.0.0.0'

# Get own machine IP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.connect(("8.8.8.8", 80))
MY_IP = sock.getsockname()[0]
sock.close()

# State variables
LEADER = ''
NEIGHBOUR = ''
SERVER_LIST = []
CLIENT_LIST = []
CLIENT_RUNNING = False
NETWORK_CHANGED = False
LEADER_CRASHED = ''
REPLICA_CRASHED = ''
