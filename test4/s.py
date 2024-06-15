import socket
import time

def start_minimal_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 9999))
    server_socket.listen(1)
    print("Minimal server listening on port 9999")

    while True:
        try:
            server_socket.settimeout(3)  # Setzt einen Timeout von 3 Sekunden
            client_socket, addr = server_socket.accept()
            print(f"Connection from {addr} has been established.")
            client_socket.send("Welcome to the server".encode())
            client_socket.close()
            break  # Beendet den Server nach erfolgreicher Verbindung
        except socket.timeout:
            print("No connection attempt in the last 3 seconds. Checking again...")

    server_socket.close()

if __name__ == "__main__":
    start_minimal_server()
