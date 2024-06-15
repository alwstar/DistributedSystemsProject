import socket

def start_minimal_client(server_ip):
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
    server_ip = input("Enter the server IP address: ")
    start_minimal_client(server_ip)
