import socket
import multiprocessing
import os

def send_broadcast(broadcast_address, broadcast_port):
    # Create a UDP socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Enable broadcast option
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    # Message sent as broadcast
    message = f'Client {os.getpid()} is looking for server'

    # Send broadcast message
    client_socket.sendto(str.encode(message), (broadcast_address, broadcast_port))
    print(f'Sent broadcast message: {message}')

    # Receive reply from server
    print('Waiting for server reply...')
    data, server = client_socket.recvfrom(1024)
    print(f'Received reply from server: {data.decode()}')

    # Use the server address and port to establish a connection
    # ...

if __name__ == '__main__':
    # Broadcast address and port
    broadcast_address = '192.168.79.255'
    broadcast_port = 10001

    # Send broadcast message
    send_broadcast(broadcast_address, broadcast_port)