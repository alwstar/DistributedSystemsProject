import socket
import common
import time

def receive_mesage():
    server_address = ('', common.SERVER_CLIENT_MESSAGE_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(server_address)
    sock.listen()
    while True:
        connection, leader_address = sock.accept()
        message = common.deserialize(connection.recv(1024))
        print(message)

def check_leader_abailability():
    global client_socket
    while True:
        try:
            data = client_socket.recv(1024)
            print(data.decode('utf-8'))
            if not data:
                print("\nChat server currently not available."
                      "Please wait 5 seconds for reconnection with new server leader.")
                client_socket.close()
                time.sleep(5)
                connect_to_server()
        except Exception as err:
            print(err)
            break

def disconnect_from_server():
    global client_socket
    message = 'disconnected'
    message = message.encode()
    client_socket.send(message)
    client_socket.close

def connect_to_server():
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    check_server_exist = request_to_join_chat()
    if check_server_exist:
        leader_address = (common.LEADER, common.SERVER_PORT_FOR_CLIENTS)
        print(f'{leader_address}: Hi, welcome to the room let me connect you...')
        client_socket.connect(leader_address)
        client_socket.send('JOIN'.encode('utf-8'))
        print(f'You can start chatting now!')
        common.new_thread(check_leader_abailability)
        while True:
            message = input("")
            try:
                client_socket.send(message.encode('utf-8'))
            except Exception as err:
                print(err)
                break
    else:
        print('Did not work trying again if possible.')
        client_socket.close()
    connect_to_server()

def request_to_join_chat():
    message = common.serialize(['JOIN', '', '', ''])
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(message, (common.MCAST_GRP, common.MCAST_PORT))
    sleep(0.5)
    try:
        data, address = sock.recvfrom(1024)
        common.LEADER = common.deserialize(data)[0]
        return True
    except socket.timeout:
        return False

if __name__ == '__main__':
    try:
        common.new_thread(receive_mesage)
        connect_to_server()
    except KeyboardInterrupt:
        print('\n You left the chat.')
        disconnect_from_server()
