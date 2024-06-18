# heartbeat.py

import socket
import sys
from time import sleep
import hosts
import ports
import leader_election

def start_heartbeat():
    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.settimeout(0.5)

        hosts.neighbour = leader_election.get_neighbour(hosts.server_list, hosts.myIP, 'right')
        host_address = (hosts.neighbour, ports.server)

        if hosts.neighbour:
            sleep(3)

            try:
                sock.connect(host_address)
                print(f'[HEARTBEAT] Neighbour {hosts.neighbour} response', file=sys.stderr)

            except:
                hosts.server_list.remove(hosts.neighbour)
                if hosts.leader == hosts.neighbour:
                    print(f'[HEARTBEAT] Server Leader {hosts.neighbour} crashed', file=sys.stderr)
                    hosts.leader_crashed = True
                    hosts.leader = ''
                    leader_election.start_leader_election()
                else:
                    print(f'[HEARTBEAT] Server Replica {hosts.neighbour} crashed', file=sys.stderr)
                    hosts.replica_crashed = True

            finally:
                sock.close()
