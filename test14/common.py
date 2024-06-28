# thread_helper.py
import threading

def newThread(target, args):
    thr = threading.Thread(target=target, args=args)
    thr.daemon = True
    thr.start()

# ports.py
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

# multicast_data.py
MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007

MULTICAST_TTL = 2

LEADER = ''
SERVER_LIST = []
CLIENT_LIST = []
CLIENT_MESSAGES = []

client_running = False
network_state = False
leader_server_crashed = ''
replica_server_crashed = ''

# server_data.py
import socket

SERVER_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
SERVER_SOCKET.connect(("8.8.8.8", 80))
SERVER_IP = SERVER_SOCKET.getsockname()[0]

LEADER_CRASH = False
LEADER_AVAILABLE = False

HEARTBEAT_RUNNING = False
HEARTBEAT_COUNT = 0

isReplicaUpdated = False
replica_data = []
