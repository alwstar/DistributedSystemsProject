import socket

def listen_for_server():
    # UDP Socket für das Empfangen von Broadcast-Nachrichten
    listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    listen_socket.bind(('', 37020))
    listen_socket.settimeout(10)  # Erhöht den Timeout-Wert auf 10 Sekunden
    print("Listening for server broadcasts")

    try:
        while True:
            data, addr = listen_socket.recvfrom(1024)
            if data.decode() == "SERVER_HERE":
                print(f"Server found at {addr[0]}")
                return addr[0]
    except socket.timeout:
        print("Server discovery timed out.")
        return None
    finally:
        listen_socket.close()

def start_minimal_client():
    server_ip = listen_for_server()
    if server_ip is None:
        print("No server found. Exiting.")
        return

    # TCP Socket für die Verbindung zum Server
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
