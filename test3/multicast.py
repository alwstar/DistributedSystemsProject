import socket

def send_multicast(message, group):
    multicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
    multicast_socket.sendto(message.encode(), group)

def receive_multicast(group, buffer_size=1024):
    multicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    multicast_socket.bind(group)
    multicast_socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                                socket.inet_aton(group[0]) + socket.inet_aton('0.0.0.0'))
    
    while True:
        data, _ = multicast_socket.recvfrom(buffer_size)
        print('Received multicast message:', data.decode())
