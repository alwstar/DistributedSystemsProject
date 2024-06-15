import socket
import time

def discover_server():
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_socket.settimeout(5)
    
    broadcast_socket.sendto("DISCOVER_SERVER".encode(), ('<broadcast>', 37020))
    
    try:
        while True:
            data, addr = broadcast_socket.recvfrom(1024)
            if data.decode() == "SERVER_HERE":
                print(f"Server found at {addr[0]}")
                return addr[0]
    except socket.timeout:
        print("Server discovery timed out.")
        return None

def start_minimal_client():
    server_ip = discover_server()
    if server_ip is None:
        print("No server found. Exiting.")
        return

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((server_ip, 9999))
        message = client_socket.recv(1024)
        print("Received from server:", message.decode())
    except socket.error as e:
        print(f"Failed to connect to the server: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    start_minimal_client()
