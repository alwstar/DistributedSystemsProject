import socket
import pickle
import time
import multicast_data
import multicast_sender
import ports
import thread_helper

def receive_message():
    server_address = ('', ports.SERVER_CLIENT_MESSAGE_PORT)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(server_address)
        sock.listen()
        while True:
            connection, _ = sock.accept()
            with connection:
                message = pickle.loads(connection.recv(1024))
                print(message)

def check_leader_availability():
    global client_socket
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                print("Chat server not available. Reconnecting in 5 seconds.")
                client_socket.close()
                time.sleep(5)
                connect_to_server()
        except Exception as err:
            print(err)
            break

def disconnect_from_server():
    global client_socket
    client_socket.send(b'disconnected')
    client_socket.close()

def connect_to_server():
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if multicast_sender.request_to_join_chat():
        leader_address = (multicast_data.LEADER, ports.SERVER_PORT_FOR_CLIENTS)
        print(f'Connecting to leader at {leader_address}...')
        client_socket.connect(leader_address)
        client_socket.send(b'JOIN')
        print('Connected. Start chatting!')
        thread_helper.new_thread(check_leader_availability, ())
        while True:
            message = input()
            try:
                client_socket.send(message.encode('utf-8'))
            except Exception as err:
                print(err)
                break
    else:
        print('Connection failed. Retrying...')
        client_socket.close()
        connect_to_server()

if __name__ == '__main__':
    try:
        thread_helper.new_thread(receive_message, ())
        connect_to_server()
    except KeyboardInterrupt:
        print('\nYou left the chat.')
        disconnect_from_server()
