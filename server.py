import socket
import threading
import random
import string
import json

clients = []
client_names = {}
leader_uid = None
my_uid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
my_ip = '127.0.0.1'
ring_port = 10001
participants = [('127.0.0.1', 10001)]  # Update with actual participant addresses

# Funktion zur dynamischen Entdeckung von Hosts
def broadcast_listener():
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    broadcast_socket.bind(('', 37020))
    print("Listening for broadcast messages on port 37020")

    while True:
        data, addr = broadcast_socket.recvfrom(1024)
        if data.decode() == "DISCOVER_SERVER":
            response_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            response_socket.sendto("SERVER_HERE".encode(), addr)

# Chat Server Funktionen (TCP)
def broadcast(message, sender_socket):
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message)
            except:
                client.close()
                clients.remove(client)

def handle_client(client_socket, addr):
    try:
        client_socket.send("Welcome! Please enter your name: ".encode())
        name = client_socket.recv(1024).decode().strip()
        client_names[client_socket] = name
        welcome_message = f"{name} has joined the chat!"
        broadcast(welcome_message.encode(), client_socket)
        print(welcome_message)

        while True:
            message = client_socket.recv(1024)
            if message:
                broadcast_message = f"{name}: {message.decode()}"
                print(broadcast_message)
                broadcast(broadcast_message.encode(), client_socket)
            else:
                client_socket.close()
                clients.remove(client_socket)
                broadcast(f"{name} has left the chat.".encode(), None)
                break
    except:
        client_socket.close()
        clients.remove(client_socket)
        broadcast(f"{name} has left the chat.".encode(), None)

def start_server():
    global leader_uid

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 9999))
    server_socket.listen(5)
    print("Server listening on port 9999")

    broadcast_thread = threading.Thread(target=broadcast_listener)
    broadcast_thread.start()

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr} has been established.")
        clients.append(client_socket)
        client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_thread.start()

if __name__ == "__main__":
    start_server()
