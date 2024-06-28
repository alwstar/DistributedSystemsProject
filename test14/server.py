import pickle
import socket
import sys
import logging
from time import sleep

import common
import thread_helper

logging.basicConfig(filename='server.log', level=logging.INFO, format='%(asctime)s:%(name)s:%(message)s')

def send_leader():
    if common.LEADER == common.SERVER_IP and len(common.SERVER_LIST) > 0:
        for i in range(len(common.SERVER_LIST)):
            replica = common.SERVER_LIST[i]
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            try:
                sock.connect((replica, common.LEADER_NOTIFICATION_PORT))
                leader_message = pickle.dumps(common.LEADER)
                sock.send(leader_message)
                logging.info(f'Leader {common.LEADER} is updating the leader parameter for {replica}')
                print(f'Updating Leader for {replica}')
            except:
                logging.critical(f'Failed to update leader address for {replica}')
                print(f'Failed to send Leader address to {replica}')
            finally:
                sock.close()

def receive_leader():
    server_address = ('', common.LEADER_NOTIFICATION_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(server_address)
    sock.listen()

    while True:
        connection, leader_address = sock.accept()
        leader = pickle.loads(connection.recv(1024))
        
        common.LEADER = leader
        print(f'LEADER IS: {common.LEADER}')

def send_server_list():
    if common.LEADER == common.SERVER_IP and len(common.SERVER_LIST) > 0:
        for i in range(len(common.SERVER_LIST)):
            if common.SERVER_LIST[i] != common.SERVER_IP:
                replica = common.SERVER_LIST[i]
                ip = replica
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sleep(1)
                try:
                    sock.connect((ip, common.SERVERLIST_UPDATE_PORT))

                    updated_list = pickle.dumps(common.SERVER_LIST)
                    sock.send(updated_list)
                    logging.info(f'Updating Server List for {ip}')
                    print(f'Updating Server List for {ip}')
                except:
                    logging.critical(f'failed to send serverlist {ip}')
                    print(f'failed to send serverlist {ip}')
                finally:
                    sock.close()

def receive_server_list():
    server_address = ('', common.SERVERLIST_UPDATE_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(server_address)
    sock.listen()

    while True:
        connection, leader_address = sock.accept()
        leader_list = pickle.loads(connection.recv(1024))

        new_list = []
        new_list = leader_list

        server_list_len = len(new_list)

        for i in range(server_list_len):
            replica = new_list[i]
            server_address = replica
            ip = server_address
            if ip == common.SERVER_IP:
                del new_list[i]
                new_list.append((leader_address[0]))
                common.SERVER_LIST = new_list
                print(f'NEW SERVER LIST {common.SERVER_LIST}')
                sleep(0.5)
                update_server_list(common.SERVER_LIST)

def send_new_client_message(ip, msg):
    if common.LEADER == common.SERVER_IP and len(common.CLIENT_LIST) > 0:
        for i in range(len(common.CLIENT_LIST)):
            client = common.CLIENT_LIST[i]
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            if ip != client:
                try:
                    sock.connect((client, common.SERVER_CLIENT_MESSAGE_PORT))
                    if ip != client:
                        packed_msg = pickle.dumps(f'from {ip}: "{msg}"')
                        sock.send(packed_msg)
                        print(f'Sending Message for {client}')
                except Exception as err:
                    print(f'Failed to send Message to {client} with following error message: {err}')
                finally:
                    sock.close()

def new_client_message(client, address):
    while True:
        try:
            data = client.recv(1024)
            if data.decode('utf-8') != "":
                print(f'{common.SERVER_IP}: new Message from {address[0]}: {data.decode("utf-8")}')
                common.CLIENT_MESSAGES.append(f'{common.SERVER_IP}: new Message from {address[0]}: {data.decode("utf-8")}')
                send_new_client_message(address[0], data.decode('utf-8'))
        except Exception as err:
            print(err)
            break

def bind_server_sock():
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        host_address = (common.SERVER_IP, common.SERVER_PORT_FOR_CLIENTS)
        print(f'Server started on IP {common.SERVER_IP} and PORT {common.SERVER_PORT_FOR_CLIENTS}')

        server_socket.bind(host_address)
        server_socket.listen()
        print(f'Server is waiting for client connections...')

        while True:
            try:
                client, address = server_socket.accept()
                client_data = client.recv(1024)

                if client_data:
                    print(f'{common.SERVER_IP}: Client {address[0]} is now connected')
                    thread_helper.newThread(new_client_message, (client, address))
            except Exception as err:
                print(err)
                break
    except socket.error as err:
        print(f'Could not start Server. Error: {err}')
        sys.exit()

def update_server_list(new_list):
    if len(common.SERVER_LIST) == 0:
        common.HEARTBEAT_RUNNING = False
        common.HEARTBEAT_COUNT = 0

        if common.LEADER != common.SERVER_IP:
            common.LEADER = common.SERVER_IP
            print(f'My server list is empty, the new leader is me {common.SERVER_IP}')

    elif len(common.SERVER_LIST) > 0:
        if common.HEARTBEAT_COUNT == 0:
            common.HEARTBEAT_COUNT += 1
            sleep(1)
            print(f'NEW LIST {list(set(new_list))}')
            common.SERVER_LIST = list(set(new_list))

            print(f'Heartbeat starting for the first time with the server list containing: {common.SERVER_LIST}')
            common.HEARTBEAT_RUNNING = True
            thread_helper.newThread(heartbeat.start_heartbeat, ())

        else:
            common.SERVER_LIST = list(set(new_list))
            common.isReplicaUpdated = True

def send_client_list():
    if common.LEADER == common.SERVER_IP and len(common.SERVER_LIST) > 0:
        for i in range(len(common.SERVER_LIST)):
            if common.SERVER_LIST[i] != common.SERVER_IP:
                ip = common.SERVER_LIST[i]
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                try:
                    sock.connect((ip, common.CLIENT_LIST_UPDATE_PORT))

                    updated_list = pickle.dumps(common.CLIENT_LIST)
                    sock.send(updated_list)
                    logging.info(f'Updating Client List for {ip}')
                    print(f'Updating Client List for {ip}')
                except:
                    logging.critical(f'failed to send Client List to {ip}')
                    print(f'failed to send Client list to {ip}')
                finally:
                    sock.close()

def receive_client_list():
    server_address = ('', common.CLIENT_LIST_UPDATE_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(server_address)
    sock.listen()

    while True:
        connection, leader_address = sock.accept()
        leader_list = pickle.loads(connection.recv(1024))

        new_list = []
        new_list = leader_list

        common.CLIENT_LIST = new_list
        print(f'NEW CLIENT LIST {common.CLIENT_LIST}')

if __name__ == '__main__':
    multicastReceiver = multicast_sender.requestToMulticast()

    if not multicastReceiver:
        common.LEADER = common.SERVER_IP
        common.LEADER_CRASH = False
        common.LEADER_AVAILABLE = True

    thread_helper.newThread(multicast_receiver.start_receiver, ())
    thread_helper.newThread(bind_server_sock, ())

    thread_helper.newThread(receive_server_list, ())
    thread_helper.newThread(receive_leader, ())
    thread_helper.newThread(heartbeat.listen_heartbeat, ())
    thread_helper.newThread(leader_election.listenforNewLeaderMessage, ())
    thread_helper.newThread(leader_election.receive_election_message, ())
    thread_helper.newThread(receive_client_list, ())

    while True:
        try:
            if common.LEADER and common.network_state:
                multicast_sender.requestToMulticast()
                common.network_state = False

            elif common.LEADER != common.SERVER_IP and common.network_state:
                common.network_state = False

        except KeyboardInterrupt:
            print(f'\nClosing Server for IP {common.SERVER_IP} on PORT {common.SERVER_PORT_FOR_CLIENTS}')
            break
