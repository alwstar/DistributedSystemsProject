# leader_election.py

import socket
import hosts
import send_broadcast

def form_ring(members):
    sorted_binary_ring = sorted([socket.inet_aton(member) for member in members])
    sorted_ip_ring = [socket.inet_ntoa(node) for node in sorted_binary_ring]
    return sorted_ip_ring

def get_neighbour(members, current_member_ip, direction='left'):
    current_member_index = members.index(current_member_ip) if current_member_ip in members else -1
    if current_member_index != -1:
        if direction == 'left':
            if current_member_index + 1 == len(members):
                return members[0]
            else:
                return members[current_member_index + 1]
        else:
            if current_member_index - 1 == 0:
                return members[0]
            else:
                return members[current_member_index - 1]
    else:
        return None

def start_leader_election(server_list, leader_server):
    ring = form_ring(server_list)
    neighbour = get_neighbour(ring, leader_server, 'right')
    new_leader = neighbour if neighbour != hosts.myIP else None
    if new_leader:
        hosts.leader = new_leader
        send_broadcast.announce_new_leader(new_leader)
    return new_leader
