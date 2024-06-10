import socket
import threading

def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024)
            if message:
                print(f"\n{message.decode()}\n> ", end='')
            else:
                print("Disconnected from server.")
                client_socket.close()
                break
        except:
            print("An error occurred.")
            client_socket.close()
            break

def discover_server():
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_socket.sendto("DISCOVER_SERVER".encode(), ('<broadcast>', 37020))

    broadcast_socket.settimeout(5)
    try:
        data, addr = broadcast_socket.recvfrom(1024)
        if data.decode() == "SERVER_HERE":
            return addr[0]
    except socket.timeout:
        print("Server discovery timed out.")
        return None

def start_client():
    server_ip = discover_server()
    if not server_ip:
        print("No server found.")
        return

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, 9999))

    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receive_thread.start()

    while True:
        message = input("> ")
        if message.lower() == 'quit':
            client_socket.close()
            break
        else:
            client_socket.send(message.encode())

if __name__ == "__main__":
    start_client()
