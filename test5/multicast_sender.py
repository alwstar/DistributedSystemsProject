import socket
import struct
import pickle
from time to sleep

import server_data
import multicast_data

broadcast_address = ('192.168.79.255', multicast_data.MCAST_PORT)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.settimeout(1)

def requestToMulticast():
    sleep(1)
    message = pickle.dumps([multicast_data.SERVER_LIST, multicast_data.LEADER])
    sock.sendto(message, broadcast_address)
    print(f'\nBroadcast sending data to receivers from {server_data.SERVER_IP} to {broadcast_address}')

    try:
        sock.recvfrom(1024)
        if multicast_data.LEADER == server_data.SERVER_IP:
            print(f'{sock.getsockname()[0]}: Sending updates to all servers\n')
        return True
    except socket.timeout:
        print(f'{server_data.SERVER_IP}: Currently no receiver reachable')
        return False

def requestToJoinChat():
    message = pickle.dumps(['JOIN', '', '', ''])
    sock.sendto(message, broadcast_address)
    sleep(0.5)
    try:
        data, address = sock.recvfrom(1024)
        multicast_data.LEADER = pickle.loads(data)[0]
        return True
    except socket.timeout:
        return False
