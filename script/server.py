import multiprocessing
import socket
import os

def broadcast_listener(server_socket, server_address, server_port):
    # Enable broadcast and reuse address options
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind socket to server address and port
    server_socket.bind((server_address, server_port))
    print(f'Server up and running at {server_address}:{server_port}')

    while True:
        # Receive broadcast message from client
        data, address = server_socket.recvfrom(1024)
        print(f'Received broadcast message "{data.decode()}" from {address[0]}:{address[1]}')

        # Send reply to client with server address and port
        reply_message = f'{server_address}:{server_port}'
        server_socket.sendto(str.encode(reply_message), address)
        print(f'Sent reply "{reply_message}" to {address[0]}:{address[1]}')

if __name__ == "__main__":
    # Create a UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Server application IP address and port
    server_address = '127.0.0.1'
    server_port = 10001

    # Start broadcast listener
    broadcast_listener(server_socket, server_address, server_port)