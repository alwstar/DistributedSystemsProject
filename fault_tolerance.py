import socket
import time

def check_server(host, port):
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.settimeout(1)
        client_socket.connect((host, port))
        client_socket.close()
        return True
    except socket.error:
        return False

def monitor_servers(server_list):
    while True:
        for server in server_list:
            host, port = server
            if check_server(host, port):
                print(f"Server {host}:{port} is up")
            else:
                print(f"Server {host}:{port} is down")
        time.sleep(5)

if __name__ == "__main__":
    servers = [('127.0.0.1', 9999)]
    monitor_servers(servers)
