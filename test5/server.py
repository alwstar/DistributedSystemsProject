import socket
import threading

broadcast_port = 37020
server_port = 10001
clients = []

def handle_client(client_socket, client_address):
    while True:
        try:
            message = client_socket.recv(1024).decode()
            if message:
                print(f"Received message from {client_address}: {message}")
                broadcast_message(f"Message from {client_address}: {message}")
        except:
            clients.remove((client_socket, client_address))
            client_socket.close()
            break

def broadcast_message(message):
    for client_socket, client_address in clients:
        try:
            client_socket.send(message.encode())
        except:
            clients.remove((client_socket, client_address))
            client_socket.close()

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("", server_port))
    server_socket.listen()
    print(f"Server listening on port {server_port}")

    while True:
        client_socket, client_address = server_socket.accept()
        clients.append((client_socket, client_address))
        print(f"Client connected from {client_address}")
        threading.Thread(target=handle_client, args=(client_socket, client_address)).start()

def listen_for_broadcast():
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    broadcast_socket.bind(("", broadcast_port))

    while True:
        data, addr = broadcast_socket.recvfrom(1024)
        message = data.decode()
        if message == "DISCOVER":
            response_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            response_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            response_socket.sendto("SERVER".encode(), addr)

if __name__ == "__main__":
    threading.Thread(target=listen_for_broadcast).start()
    start_server()
