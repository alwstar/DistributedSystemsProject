import pickle
import socket
import struct
import multicast_data
import server
import server_data

MULTICAST_IP = multicast_data.MCAST_GRP
SERVER_ADDRESS = ('', multicast_data.MCAST_PORT)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def setup_multicast_socket():
    sock.bind(SERVER_ADDRESS)
    group = socket.inet_aton(MULTICAST_IP)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    print(f'\n{server_data.SERVER_IP}: Started UDP Socket on Port {multicast_data.MCAST_PORT}')

def handle_client_connection(data, address):
    if multicast_data.LEADER == server_data.SERVER_IP and data[0] == 'JOIN':
        if address[0] not in multicast_data.CLIENT_LIST:
            multicast_data.CLIENT_LIST.append(address[0])
        response = [multicast_data.LEADER, '']
        sock.sendto(pickle.dumps(response), address)
        server.send_client_list()
        print(f'{server_data.SERVER_IP}: "{address}" wants to join the Chat Room\n')

def handle_replica_connection(data, address):
    if not data[0]:
        if address[0] not in multicast_data.SERVER_LIST:
            multicast_data.SERVER_LIST.append(address[0])
        server_data.replica_data.append(address)
        server.update_server_list(multicast_data.SERVER_LIST)
        server.send_server_list()
        server.send_leader()
        sock.sendto('ack'.encode('utf-8'), address)
        multicast_data.network_state = True
        print(f'{server_data.SERVER_IP}: Replica server joined {address}')

def start_receiver():
    setup_multicast_socket()
    while True:
        try:
            data, address = sock.recvfrom(1024)
            data = pickle.loads(data)
            if address[0] != server_data.SERVER_IP:
                print(f'{server_data.SERVER_IP}: Received data from {address} \n')
                handle_client_connection(data, address)
                handle_replica_connection(data, address)
        except KeyboardInterrupt:
            sock.close()
            print(f'{server_data.SERVER_IP}: Closing Socket')

if __name__ == '__main__':
    start_receiver()
