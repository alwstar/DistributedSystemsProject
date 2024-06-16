# Server Operations

import socket
import sys
import threading
import queue
from config import *
from network import send_multicast, start_multicast_receiver, start_heartbeat
from election.py import start_leader_election

# Queue for messages
FIFO = queue.Queue()

# Printer function for server info
def printer():
    print(f'\n[SERVER] Server List: {SERVER_LIST} ==> Leader: {LEADER}'
          f'\n[SERVER] Client List: {CLIENT_LIST}'
          f'\n[SERVER] Neighbour ==> {NEIGHBOUR}\n')

# Handle client messages
def client_handler(client, address):
    while True:
        try:
            data = client.recv(BUFFER_SIZE)
            if not data:
                CLIENT_LIST.remove(client)
                client.close()
                break
            FIFO.put(f'{address} said: {data.decode(UNICODE)}')
        except:
            break

# Send messages to all clients
def send_clients():
    while not FIFO.empty():
        message = FIFO.get()
        for member in CLIENT_LIST:
            member.send(message.encode(UNICODE))

# Bind and start listening for connections
def start_binding():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((MY_IP, SERVER_PORT))
    sock.listen()
    while True:
        client, address = sock.accept()
        CLIENT_LIST.append(client)
        threading.Thread(target=client_handler, args=(client, address)).start()

# Main server logic
if __name__ == '__main__':
    threading.Thread(target=start_multicast_receiver).start()
    threading.Thread(target=start_binding).start()
    threading.Thread(target=start_heartbeat).start()
    while True:
        if LEADER == MY_IP and (NETWORK_CHANGED or REPLICA_CRASHED):
            send_multicast([SERVER_LIST, LEADER, LEADER_CRASHED, REPLICA_CRASHED, CLIENT_LIST])
            NETWORK_CHANGED = False
            REPLICA_CRASHED = ''
            printer()
        send_clients()
