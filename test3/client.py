import socket
import uuid
from discovery import broadcast
from multicast import send_multicast

def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = broadcast()
    server_port = 10002
    buffer_size = 1024
    message = 'Hi server from ' + str(uuid.uuid4())

    client_socket.sendto(message.encode(), (server_address, server_port))
    print('Sent to server: ', message)

    data, _ = client_socket.recvfrom(buffer_size)
    print('Received message from server: ', data.decode())

if __name__ == "__main__":
    start_client()
