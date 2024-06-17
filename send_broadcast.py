# send_broadcast.py

import socket
import sys
import pickle
from time import sleep
import hosts
import ports

broadcast_address = (hosts.broadcast, ports.broadcast)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.settimeout(1)

def sending_request_to_broadcast():
    sleep(1)
    message = pickle.dumps([hosts.server_list, hosts.leader, hosts.leader_crashed, hosts.replica_crashed, str(hosts.client_list)])
    sock.sendto(message, broadcast_address)
    print(f'\n[BROADCAST SENDER {hosts.myIP}] Sending data to Broadcast Receivers {broadcast_address}', file=sys.stderr)

    try:
        sock.recvfrom(hosts.buffer_size)
        if hosts.leader == hosts.myIP:
            print(f'[BROADCAST SENDER {hosts.myIP}] All Servers have been updated\n', file=sys.stderr)
        return True
    except socket.timeout:
        print(f'[BROADCAST SENDER {hosts.myIP}] Broadcast Receiver not detected', file=sys.stderr)
        return False

def sending_join_chat_request_to_broadcast():
    print(f'\n[BROADCAST SENDER {hosts.myIP}] Sending join chat request to Broadcast Address {broadcast_address}', file=sys.stderr)
    message = pickle.dumps(['JOIN', '', '', ''])
    sock.sendto(message, broadcast_address)

    try:
        data, address = sock.recvfrom(hosts.buffer_size)
        hosts.leader = pickle.loads(data)[0]
        return True
    except socket.timeout:
        print(f'[BROADCAST SENDER {hosts.myIP}] Broadcast Receiver not detected -> Chat Server is offline.', file=sys.stderr)
        return False
