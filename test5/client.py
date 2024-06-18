import socket
import threading
import time

broadcast_port = 37020
server_ip = None
server_port = 10001

def receive_messages(sock):
    while True:
        try:
            message = sock.recv(1024).decode()
            if message:
                print(f"Received: {message}")
        except:
            break

def discover_server():
    global server_ip
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    client_socket.sendto("DISCOVER".encode(), ('<broadcast>', broadcast_port))

    client_socket.settimeout(5)
    try:
        while server_ip is None:
            data, addr = client_socket.recvfrom(1024)
            if data.decode() == "SERVER":
                server_ip = addr[0]
                print(f"Discovered server at {server_ip}")
    except socket.timeout:
        print("Server discovery timeout.")
    finally:
        client_socket.close()

def connect_to_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, server_port))
    threading.Thread(target=receive_messages, args=(sock,)).start()
    while True:
        message = input("")
        if message:
            sock.send(message.encode())

if __name__ == "__main__":
    discover_server()
    if server_ip:
        connect_to_server()
