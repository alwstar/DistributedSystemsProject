import socket
import threading
import time
from multicast import request_to_join_chat, LEADER

def receive_message():
    server_address = ('', 9999)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(server_address)
    sock.listen()
    while True:
        connection, leader_address = sock.accept()
        message = connection.recv(1024).decode('utf-8')
        print(message)

def check_leader_availability():
    global client_socket
    while True:
        try:
            data = client_socket.recv(1024)
            if not data:
                print("\nChat server currently not available. Reconnecting...")
                client_socket.close()
                time.sleep(5)
                connect_to_server()
        except Exception as err:
            print(err)
            break

def disconnect_from_server():
    global client_socket
    client_socket.send('disconnected'.encode())
    client_socket.close()

def connect_to_server():
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if request_to_join_chat():
        leader_address = (LEADER, 9999)
        client_socket.connect(leader_address)
        client_socket.send('JOIN'.encode())
        threading.Thread(target=check_leader_availability).start()
        while True:
            message = input("")
            client_socket.send(message.encode('utf-8'))
    else:
        client_socket.close()
        connect_to_server()

if __name__ == '__main__':
    try:
        threading.Thread(target=receive_message).start()
        connect_to_server()
    except KeyboardInterrupt:
        disconnect_from_server()
