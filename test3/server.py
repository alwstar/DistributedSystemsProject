import socket
import multiprocessing
import json
import os
from discovery import broadcast_listener
from leader_election import start_election, handle_election_message, send_election_message
from multicast import send_multicast, receive_multicast

class Server(multiprocessing.Process):
    def __init__(self, server_socket, received_data, client_address):
        super(Server, self).__init__()
        self.server_socket = server_socket
        self.received_data = received_data
        self.client_address = client_address

    def run(self):
        message = 'Hi ' + self.client_address[0] + ':' + str(self.client_address[1]) + '. This is server with process ID' + str(os.getpid())
        self.server_socket.sendto(str.encode(message), self.client_address)
        print('Sent to client: ', message)

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = '0.0.0.0'
    server_port = 10002
    buffer_size = 1024

    server_socket.bind((server_address, server_port))
    print('Server up and running at {}:{}'.format(server_address, server_port))

    discovery_process = multiprocessing.Process(target=broadcast_listener, args=(server_socket,))
    discovery_process.start()

    while True:
        data, address = server_socket.recvfrom(buffer_size)
        print('Received message \'{}\' at {}:{}'.format(data.decode(), address[0], address[1]))
        p = Server(server_socket, data, address)
        p.start()
        p.join()

if __name__ == "__main__":
    start_server()
