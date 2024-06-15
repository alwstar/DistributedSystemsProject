import socket
import struct
import pickle
from time import sleep

MCAST_GRP = '224.1.1.1'
MCAST_PORT = 5007
MULTICAST_TTL = 2

LEADER = ''
SERVER_LIST = []
CLIENT_LIST = []
CLIENT_MESSAGES = []

multicastAddress = (MCAST_GRP, MCAST_PORT)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(1)
ttl = struct.pack('b', MULTICAST_TTL)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

def request_to_multicast():
    sleep(1)
    message = pickle.dumps([SERVER_LIST, LEADER])
    sock.sendto(message, multicastAddress)
    print(f'\nMulticast sending data to receivers from server to {multicastAddress}')
    try:
        sock.recvfrom(1024)
        if LEADER:
            print(f'Sending updates to all servers\n')
        return True
    except socket.timeout:
        print(f'Currently no receiver reachable')
        return False

def request_to_join_chat():
    message = pickle.dumps(['JOIN', '', '', ''])
    sock.sendto(message, multicastAddress)
    sleep(0.5)
    try:
        data, address = sock.recvfrom(1024)
        LEADER = pickle.loads(data)[0]
        return True
    except socket.timeout:
        return False

def start_receiver():
    sock.bind(('', MCAST_PORT))
    group = socket.inet_aton(MCAST_GRP)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    print(f'Started UDP Socket to listen on Port {MCAST_PORT}')
    while True:
        try:
            data, address = sock.recvfrom(1024)
            if address[0] != SERVER_IP:
                print(f'Received data from {address}')
            if LEADER == SERVER_IP and pickle.loads(data)[0] == 'JOIN':
                CLIENT_LIST.append(address[0]) if address[0] not in CLIENT_LIST else CLIENT_LIST
                message = pickle.dumps([LEADER, ''])
                sock.sendto(message, address)
                send_client_list()
        except KeyboardInterrupt:
            sock.close()
            print(f'Closing Socket')
