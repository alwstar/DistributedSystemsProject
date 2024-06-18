import socket
import json
import hosts
import ports

def form_ring(members):
    sorted_binary_ring = sorted([socket.inet_aton(member) for member in members])
    sorted_ip_ring = [socket.inet_ntoa(node) for node in sorted_binary_ring]
    return sorted_ip_ring

def get_neighbour(members, current_member_ip, direction='left'):
    current_member_index = members.index(current_member_ip) if current_member_ip in members else -1
    if current_member_index!= -1:
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

def start_leader_election():
    ring = form_ring(hosts.server_list)
    neighbour = get_neighbour(ring, hosts.myIP, 'right')

    election_message = {
        "mid": hosts.myIP,
        "isLeader": False
    }
    hosts.participant = True
    send_election_message(neighbour, election_message)

def send_election_message(neighbour, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    message = json.dumps(message).encode(hosts.unicode)
    sock.sendto(message, (neighbour, ports.server))
    sock.close()

def receive_election_message():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((hosts.myIP, ports.server))

    while True:
        data, address = sock.recvfrom(hosts.buffer_size)
        election_message = json.loads(data.decode(hosts.unicode))

        if election_message['isLeader']:
            hosts.leader = election_message['mid']
            hosts.participant = False
            print(f"New Leader elected: {hosts.leader}")
            if hosts.leader!= hosts.myIP:
                print("I'm not the leader, stopping my server")
                # Stop your server here
        elif election_message['mid'] == hosts.myIP:
            election_message['isLeader'] = True
            send_election_message(get_neighbour(hosts.server_list, hosts.myIP, 'right'), election_message)
        elif election_message['mid'] < hosts.myIP and not hosts.participant:
            election_message = {
                "mid": hosts.myIP,
                "isLeader": False
            }
            hosts.participant = True
            send_election_message(get_neighbour(hosts.server_list, hosts.myIP, 'right'), election_message)
        elif election_message['mid'] > hosts.myIP:
            send_election_message(get_neighbour(hosts.server_list, hosts.myIP, 'right'), election_message)

if __name__ == '__main__':
    start_leader_election()
    receive_election_message()