import socket
import pickle
import multicast_data
import ports
import server_data
from server import update_server_list

def form_ring(members):
    return [socket.inet_ntoa(node) for node in sorted([socket.inet_aton(member) for member in members])]

def get_neighbour(ring, current_node_ip, direction='left'):
    idx = ring.index(current_node_ip)
    if direction == 'left':
        return ring[0] if idx + 1 == len(ring) else ring[idx + 1]
    return ring[-1] if idx == 0 else ring[idx - 1]

def send_new_leader_message():
    if multicast_data.LEADER == server_data.SERVER_IP:
        msg = server_data.SERVER_IP
        for ip in multicast_data.SERVER_LIST:
            try:
                with socket.create_connection((ip, ports.NEW_LEADER_PORT), timeout=2) as s:
                    s.send(msg.encode())
                    response = s.recv(1024).decode()
                    print(f'Ack from {ip}: {response}')
            except socket.timeout:
                pass

def listen_for_new_leader_message():
    server_address = ('', ports.NEW_LEADER_PORT)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(server_address)
        s.listen()
        print(f'Listening for new leader message on Port: {ports.NEW_LEADER_PORT}')
        while True:
            connection, _ = s.accept()
            with connection:
                new_leader_ip = connection.recv(1024).decode()
                multicast_data.LEADER = new_leader_ip
                connection.send(b'ack msg. Received new leader information')
                print(f'New leader is: {new_leader_ip}')

def start_leader_election(server_list, ip):
    participants = [ip] + server_list
    if len(server_list) == 1:
        send_election_message(ip, server_list[0])
    else:
        ring = form_ring(participants)
        neighbour = get_neighbour(ring, ip, 'right')
        send_election_message(ip, neighbour)

def send_election_message(msg, neighbour):
    try:
        with socket.create_connection((neighbour, ports.SERVER_ELECTION_PORT), timeout=2) as s:
            s.send(msg.encode())
            print(f'Sent election message to {neighbour}: "{msg}"')
    except:
        print(f'Failed to send message to {neighbour}')

def receive_election_message():
    server_address = ('', ports.SERVER_ELECTION_PORT)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(server_address)
        sock.listen()
        while True:
            conn, _ = sock.accept()
            with conn:
                response = conn.recv(1024).decode()
                print(f'Received {response} from leader election')
                if response == server_data.SERVER_IP:
                    multicast_data.LEADER = server_data.SERVER_IP
                    send_new_leader_message()
                elif response > server_data.SERVER_IP:
                    send_election_message(response, get_neighbour(form_ring(multicast_data.SERVER_LIST), server_data.SERVER_IP, 'right'))
                else:
                    print(f'Received IP is not higher than mine.')

if __name__ == '__main__':
    listen_for_new_leader_message()
    receive_election_message()
