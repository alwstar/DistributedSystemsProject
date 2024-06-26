import pickle
import socket
import sys
import logging
from time import sleep
import heartbeat
import leader_election
import multicast_data
import multicast_receiver
import multicast_sender
import ports
import server_data
import thread_helper

logging.basicConfig(filename='server.log', level=logging.INFO, format='%(asctime)s:%(name)s:%(message)s')

def send_data_to_replicas(port, data):
    for replica in multicast_data.SERVER_LIST:
        if replica != server_data.SERVER_IP:
            try:
                with socket.create_connection((replica, port), timeout=3) as sock:
                    sock.send(pickle.dumps(data))
                    logging.info(f'Sent data to {replica} on port {port}')
            except Exception as e:
                logging.critical(f'Failed to send data to {replica} on port {port}: {e}')

def send_leader():
    if multicast_data.LEADER == server_data.SERVER_IP:
        send_data_to_replicas(ports.LEADER_NOTIFICATION_PORT, multicast_data.LEADER)

def send_server_list():
    if multicast_data.LEADER == server_data.SERVER_IP:
        send_data_to_replicas(ports.SERVERLIST_UPDATE_PORT, multicast_data.SERVER_LIST)

def send_client_list():
    if multicast_data.LEADER == server_data.SERVER_IP:
        send_data_to_replicas(ports.CLIENT_LIST_UPDATE_PORT, multicast_data.CLIENT_LIST)

def receive_data(port, handler):
    server_address = ('', port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(server_address)
        sock.listen()
        while True:
            conn, _ = sock.accept()
            with conn:
                data = pickle.loads(conn.recv(1024))
                handler(data)

def handle_leader_data(data):
    multicast_data.LEADER = data
    print(f'LEADER IS: {multicast_data.LEADER}')

def handle_server_list_data(data):
    multicast_data.SERVER_LIST = list(set(data))
    print(f'NEW SERVER LIST {multicast_data.SERVER_LIST}')
    update_server_list(multicast_data.SERVER_LIST)

def handle_client_list_data(data):
    multicast_data.CLIENT_LIST = list(set(data))
    print(f'NEW CLIENT LIST {multicast_data.CLIENT_LIST}')

def handle_client_message(client, address):
    while True:
        try:
            data = client.recv(1024).decode('utf-8')
            if data:
                print(f'{server_data.SERVER_IP}: New message from {address[0]}: {data}')
                multicast_data.CLIENT_MESSAGES.append(data)
                send_new_client_message(address[0], data)
        except Exception as e:
            print(e)
            break

def send_new_client_message(ip, msg):
    if multicast_data.LEADER == server_data.SERVER_IP:
        for client in multicast_data.CLIENT_LIST:
            if ip != client:
                try:
                    with socket.create_connection((client, ports.SERVER_CLIENT_MESSAGE_PORT), timeout=3) as sock:
                        sock.send(pickle.dumps(f'from {ip}: "{msg}"'))
                        print(f'Sent message to {client}')
                except Exception as e:
                    print(f'Failed to send message to {client}: {e}')

def start_server():
    print(f'Server started on IP {server_data.SERVER_IP} and PORT {ports.SERVER_PORT_FOR_CLIENTS}')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((server_data.SERVER_IP, ports.SERVER_PORT_FOR_CLIENTS))
        server_socket.listen()
        print('Server is waiting for client connections...')
        while True:
            client, address = server_socket.accept()
            thread_helper.new_thread(handle_client_message, (client, address))

def update_server_list(new_list):
    if not multicast_data.SERVER_LIST:
        multicast_data.LEADER = server_data.SERVER_IP
        server_data.HEARTBEAT_RUNNING = False
        server_data.HEARTBEAT_COUNT = 0
    elif server_data.HEARTBEAT_COUNT == 0:
        server_data.HEARTBEAT_COUNT += 1
        multicast_data.SERVER_LIST = list(set(new_list))
        thread_helper.new_thread(heartbeat.start_heartbeat, ())
    else:
        multicast_data.SERVER_LIST = list(set(new_list))
        server_data.isReplicaUpdated = True

if __name__ == '__main__':
    if not multicast_sender.request_to_multicast():  # Corrected function call
        multicast_data.LEADER = server_data.SERVER_IP
        server_data.LEADER_CRASH = False
        server_data.LEADER_AVAILABLE = True

    thread_helper.new_thread(multicast_receiver.start_receiver, ())
    thread_helper.new_thread(start_server, ())
    thread_helper.new_thread(receive_data, (ports.SERVERLIST_UPDATE_PORT, handle_server_list_data))
    thread_helper.new_thread(receive_data, (ports.LEADER_NOTIFICATION_PORT, handle_leader_data))
    thread_helper.new_thread(receive_data, (ports.CLIENT_LIST_UPDATE_PORT, handle_client_list_data))
    thread_helper.new_thread(heartbeat.listen_heartbeat, ())
    thread_helper.new_thread(leader_election.listen_for_new_leader_message, ())
    thread_helper.new_thread(leader_election.receive_election_message, ())

    while True:
        try:
            if multicast_data.LEADER and multicast_data.network_state:
                multicast_sender.request_to_multicast()  # Corrected function call
                multicast_data.network_state = False
        except KeyboardInterrupt:
            print(f'\nClosing Server for IP {server_data.SERVER_IP} on PORT {ports.SERVER_PORT_FOR_CLIENTS}')
            break
