import socket
import json
import struct
import threading
from time import sleep

MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007
MULTICAST_TTL = 2

MULTICAST = 10000
SERVER_PORT_FOR_CLIENTS = 10001
SERVERLIST_UPDATE_PORT = 8090
LEADER_NOTIFICATION_PORT = 8100
SERVER_CLIENT_MESSAGE_PORT = 8110
SERVER_TO_CLIENT_MESSAGE_PORT = 8120
SERVER_ELECTION_PORT = 8130
CLIENT_CONNECTION_PORT = 8010
CLIENT_MESSAGE_PORT = 8020
CLIENT_LIST_UPDATE_PORT = 8030
HEARTBEAT_PORT = 8060
NEW_LEADER_PORT = 8070

LEADER = ''
SERVER_LIST = []
CLIENT_LIST = []
CLIENT_MESSAGES = []

client_running = False
network_state = False
leader_server_crashed = ''
replica_server_crashed = ''

def new_thread(target, args=()):
    thr = threading.Thread(target=target, args=args)
    thr.daemon = True
    thr.start()

def serialize(data):
    return json.dumps(data).encode('utf-8')

def deserialize(data):
    return json.loads(data.decode('utf-8'))

# Global server data
SERVER_IP = socket.gethostbyname(socket.gethostname())
LEADER_CRASH = False
LEADER_AVAILABLE = False
HEARTBEAT_RUNNING = False
HEARTBEAT_COUNT = 0
isReplicaUpdated = False
replica_data = []
