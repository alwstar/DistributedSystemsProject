# Network and Communication

import socket
import sys
import struct
import pickle
from time import sleep
from config import *

# Multicast Sender
def send_multicast(message):
    multicast_address = (MULTICAST_IP, MULTICAST_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    sock.settimeout(1)
    sock.sendto(pickle.dumps(message), multicast_address)
    try:
        sock.recvfrom(BUFFER_SIZE)
        return True
    except socket.timeout:
        return False

# Multicast Receiver
def start_multicast_receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', MULTICAST_PORT))
    group = socket.inet_aton(MULTICAST_IP)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    while True:
        try:
            data, address = sock.recvfrom(BUFFER_SIZE)
            handle_multicast_message(data, address)
        except KeyboardInterrupt:
            sock.close()
            break

def handle_multicast_message(data, address):
    message = pickle.loads(data)
    # Handle the received multicast message
    pass

# Heartbeat Mechanism
def start_heartbeat():
    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(0.5)
        neighbour = get_neighbour(SERVER_LIST, MY_IP, 'right')
        if neighbour:
            try:
                sock.connect((neighbour, SERVER_PORT))
            except:
                SERVER_LIST.remove(neighbour)
                if LEADER == neighbour:
                    global LEADER
                    LEADER = MY_IP
                    NETWORK_CHANGED = True
            finally:
                sock.close()
        sleep(3)
