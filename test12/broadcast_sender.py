# broadcast_sender.py
import socket
import struct

import server_data
import ports
import broadcast_data
import pickle
from time import sleep

# global variable definitions for broadcast sender
broadcastAddress = (broadcast_data.BCAST_GRP, broadcast_data.BCAST_PORT)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

# will be sent when a new connection applied and established
def requestToBroadcast():
    sleep(1)
    message = pickle.dumps([broadcast_data.SERVER_LIST, broadcast_data.LEADER])
    sock.sendto(message, broadcastAddress)
    print(f'\nBroadcasting data to receivers from {server_data.SERVER_IP} to {broadcastAddress}')

    try:
        sock.recvfrom(1024)
        if broadcast_data.LEADER == server_data.SERVER_IP:
            print(f'{sock.getsockname()[0]}: Sending updates to all servers\n')
        return True
    except socket.timeout:
        print(f'{server_data.SERVER_IP}: Currently no receiver reachable')
        return False

# sent by clients join requests
def requestToJoinChat():
    message = pickle.dumps(['JOIN', '', '', ''])
    sock.sendto(message, broadcastAddress)
    sleep(0.5)
    try:
        data, address = sock.recvfrom(1024)
        broadcast_data.LEADER = pickle.loads(data)[0]
        return True
    except socket.timeout:
        return False
