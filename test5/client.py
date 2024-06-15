import socket
import threading
import json
import time

server_ip = None
server_port = 9999

def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024)
            if message:
                print(f"\n{message.decode()}\n> ", end='')
            else:
                print("Disconnected from server.")
                client_socket.close()
                reconnect_to_leader()
                break
        except:
            print("An error occurred.")
            client_socket.close()
            reconnect_to_leader()
            break

def discover_server():
    global server_ip
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_socket.sendto("DISCOVER_SERVER".encode(), ('<broadcast>', 37020))

    broadcast_socket.settimeout(5)
    try:
        data, addr = broadcast_socket.recvfrom(1024)
        if data.decode() == "SERVER_HERE":
            server_ip = addr[0]
            return server_ip
    except socket.timeout:
        print("Server discovery timed out.")
        return None

def reconnect_to_leader():
    while True:
        print("Attempting to reconnect to leader...")
        if discover_server():
            start_client()
            break
        else:
            print("No leader found. Retrying in 5 seconds...")
            time.sleep(5)

def start_client():
    global server_ip
    if not server_ip:
        server_ip = discover_server()
        if not server_ip:
            print("No server found.")
            return

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))

    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.start()

    name = input("Please enter your name: ")
    client_socket.send(name.encode())

    while True:
        message = input("> ")
        if message.lower() == 'quit':
            client_socket.close()
            break
        else:
            client_socket.send(message.encode())

if __name__ == "__main__":
    start_client()
