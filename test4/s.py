import socket
import time

def start_minimal_server():
    # TCP Socket für den Server
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 9999))
    server_socket.listen(1)
    print("Minimal server listening on port 9999")

    # UDP Socket für Broadcast-Nachrichten
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    broadcast_address = '192.168.178.255'  # Beispiel: '255.255.255.255' oder '192.168.1.255'

    while True:
        try:
            server_socket.settimeout(3)  # Setzt einen Timeout von 3 Sekunden
            client_socket, addr = server_socket.accept()
            print(f"Connection from {addr} has been established.")
            client_socket.send("Welcome to the server".encode())
            client_socket.close()
            break  # Beendet den Server nach erfolgreicher Verbindung
        except socket.timeout:
            # Senden einer Broadcast-Nachricht, um den Clients die Anwesenheit des Servers mitzuteilen
            broadcast_socket.sendto("SERVER_HERE".encode(), (broadcast_address, 37020))
            print("Broadcasting SERVER_HERE message")

    server_socket.close()
    broadcast_socket.close()

if __name__ == "__main__":
    start_minimal_server()
