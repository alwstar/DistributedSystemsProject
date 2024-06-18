# receive_broadcast.py

import socket
import sys
import pickle
import hosts
import ports
import leader_election

broadcast_ip = hosts.broadcast
server_address = ('', ports.broadcast)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
sock.bind(server_address)

def starting_broadcast_receiver():
    print(f'\n[BROADCAST RECEIVER {hosts.myIP}] Starting UDP Socket and listening on Port {ports.broadcast}', file=sys.stderr)

    while True:
        try:
            data, address = sock.recvfrom(hosts.buffer_size)
            print(f'\n[BROADCAST RECEIVER {hosts.myIP}] Received data from {address}\n', file=sys.stderr)

            if hosts.leader == hosts.myIP and pickle.loads(data)[0] == 'JOIN':
                message = pickle.dumps([hosts.leader, ''])
                sock.sendto(message, address)
                print(f'[BROADCAST RECEIVER {hosts.myIP}] Client {address} wants to join the Chat Room\n', file=sys.stderr)

            if len(pickle.loads(data)[0]) == 0:
                hosts.server_list.append(address[0]) if address[0] not in hosts.server_list else hosts.server_list
                sock.sendto('ack'.encode(hosts.unicode), address)
                hosts.network_changed = True

            elif pickle.loads(data)[1] and hosts.leader != hosts.myIP or pickle.loads(data)[3]:
                hosts.server_list = pickle.loads(data)[0]
                hosts.leader = pickle.loads(data)[1]
                hosts.client_list = pickle.loads(data)[4]
                print(f'[BROADCAST RECEIVER {hosts.myIP}] All Data have been updated', file=sys.stderr)

                sock.sendto('ack'.encode(hosts.unicode), address)
                hosts.network_changed = True

        except KeyboardInterrupt:
            print(f'[BROADCAST RECEIVER {hosts.myIP}] Closing UDP Socket', file=sys.stderr)
        finally:
            if hosts.leader_crashed:
                leader_election.start_leader_election()
