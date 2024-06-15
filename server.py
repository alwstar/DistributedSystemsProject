import socket
import threading
import random
import string
import json
import time

clients = []
client_names = {}
server_name = "Server"
my_ip = '127.0.0.1'
ring_port = 10001

# Funktion zur dynamischen Entdeckung von Hosts
def discover_other_servers():
    global server_name
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_socket.settimeout(2)
    
    server_count = 1
    try:
        for i in range(5):
            broadcast_socket.sendto("DISCOVER_SERVER".encode(), ('<broadcast>', 37020))
            while True:
                try:
                    data, addr = broadcast_socket.recvfrom(1024)
                    if data.decode() == "SERVER_HERE":
                        server_count += 1
                except socket.timeout:
                    break
    except Exception as e:
        print(f"Error discovering other servers: {e}")

    server_name = f"Server{server_count}"
    print(f"{server_name} is running.")

# Broadcast listener für eingehende Discovery-Anfragen
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
        if client_socket in client_names:
            name = client_names.pop(client_socket)
            broadcast(f"{name} has left the chat.".encode(), None)

def log_status():
    while True:
        print(f"{server_name} is active.")
        print("Current clients:")
        for name in client_names.values():
            print(f" - {name}")
        time.sleep(10)  # Log status every 10 seconds

def start_server():
    global server_name

    discover_other_servers()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 9999))
    server_socket.listen(5)
    print(f"{server_name} listening on port 9999")

    broadcast_thread = threading.Thread(target=broadcast_listener)
    broadcast_thread.start()

    log_thread = threading.Thread(target=log_status)
    log_thread.start()

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr} has been established.")
        client_socket.send(f"Connected to {server_name}".encode())
        clients.append(client_socket)
        client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_thread.start()

if __name__ == "__main__":
    start_server()
