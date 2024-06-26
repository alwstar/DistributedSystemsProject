import socket
import struct
import pickle
from time import sleep
import server_data
import ports
import multicast_data

MULTICAST_ADDRESS = (multicast_data.MCAST_GRP, multicast_data.MCAST_PORT)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.settimeout(1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, struct.pack('b', 1))

def send_multicast(data):
    message = pickle.dumps(data)
    sock.sendto(message, MULTICAST_ADDRESS)
    print(f'\nSent multicast data from {server_data.SERVER_IP} to {MULTICAST_ADDRESS}')
    try:
        sock.recvfrom(1024)
        if multicast_data.LEADER == server_data.SERVER_IP:
            print(f'{sock.getsockname()[0]}: Sending updates to all servers\n')
        return True
    except socket.timeout:
        print(f'{server_data.SERVER_IP}: No receiver reachable')
        return False

def request_to_multicast():
    sleep(1)
    data = [multicast_data.SERVER_LIST, multicast_data.LEADER]
    return send_multicast(data)

def request_to_join_chat():
    print("Sending join request to multicast group...")
    data = ['JOIN', '', '', '']
    sock.sendto(pickle.dumps(data), MULTICAST_ADDRESS)
    sleep(0.5)
    try:
        data, address = sock.recvfrom(1024)
        multicast_data.LEADER = pickle.loads(data)[0]
        print(f"Join request acknowledged by leader at {multicast_data.LEADER}")
        return True
    except socket.timeout:
        print("Join request timed out, no response from leader.")
        return False
