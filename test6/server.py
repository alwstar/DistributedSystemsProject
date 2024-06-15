import socket
import threading
from multicast import request_to_multicast, start_receiver
from heartbeat_leader import start_heartbeat, receive_election_message, receive_new_leader_message

clients = []
SERVER_IP = '127.0.0.1'

def start_server():
    threading.Thread(target=request_to_multicast).start()
    threading.Thread(target=start_heartbeat).start()
    threading.Thread(target=receive_election_message).start()
    threading.Thread(target=receive_new_leader_message).start()
    threading.Thread(target=start_receiver).start()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 9999))
    server_socket.listen(5)

    while True:
        client_socket, addr = server_socket.accept()
        clients.append(client_socket)
        threading.Thread(target=handle_client, args=(client_socket, addr)).start()

def handle_client(client_socket, addr):
    try:
        client_socket.send("Welcome! Please enter your name: ".encode())
        name = client_socket.recv(1024).decode().strip()
        while True:
            message = client_socket.recv(1024)
            if message:
                broadcast(message, client_socket)
            else:
                client_socket.close()
                break
    except:
        client_socket.close()

def broadcast(message, sender_socket):
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message)
            except:
                client.close()
                clients.remove(client)

if __name__ == "__main__":
    start_server()
