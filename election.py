# Leader Election

import socket

def form_ring(members):
    sorted_binary_ring = sorted([socket.inet_aton(member) for member in members])
    return [socket.inet_ntoa(node) for node in sorted_binary_ring]

def get_neighbour(members, current_member_ip, direction='left'):
    current_member_index = members.index(current_member_ip) if current_member_ip in members else -1
    if current_member_index != -1:
        if direction == 'left':
            return members[0] if current_member_index + 1 == len(members) else members[current_member_index + 1]
        else:
            return members[0] if current_member_index - 1 == 0 else members[current_member_index - 1]
    return None

def start_leader_election(server_list, leader_server):
    ring = form_ring(server_list)
    return get_neighbour(ring, leader_server, 'right') if leader_server != MY_IP else None
