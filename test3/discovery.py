import socket

def broadcast():
    BROADCAST_IP = " 192.168.79.255"
    BROADCAST_PORT = 5973
    MY_IP = socket.gethostbyname(socket.gethostname())
    message = MY_IP + ' sent a broadcast message'

    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_socket.sendto(message.encode(), (BROADCAST_IP, BROADCAST_PORT))

    return MY_IP

def broadcast_listener(server_socket):
    BROADCAST_PORT = 5973
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    listen_socket.bind(('', BROADCAST_PORT))

    while True:
        data, addr = listen_socket.recvfrom(1024)
        print("Received broadcast message:", data.decode())
        server_socket.sendto(data, addr)
