import socket
import threading
import pickle
import multicast_data
import ports
import time
from heartbeat import listen_for_heartbeat, send_heartbeat
from multicast_receiver import multicast_listener
from multicast_sender import notify_server_list_update, notify_leader_election

def handle_client_connection(client_socket, address):
    """
    Handles incoming client connections.
    """
    try:
        while True:
            data = client_socket.recv(1024)
            if not data:
                break
            # Echo the received message to all clients
            for client in multicast_data.CLIENT_LIST:
                if client != address:
                    client.sendall(data)
    finally:
        client_socket.close()
        multicast_data.CLIENT_LIST.remove(address)
        print(f"Client {address} disconnected.")

def accept_client_connections():
    """
    Accepts new client connections and handles them with a new thread.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', ports.SERVER_PORT_FOR_CLIENTS))
    server_socket.listen()

    while True:
        client_socket, addr = server_socket.accept()
        multicast_data.CLIENT_LIST.append(client_socket)
        print(f"New client connected: {addr}")
        threading.Thread(target=handle_client_connection, args=(client_socket, addr)).start()

def main():
    threading.Thread(target=listen_for_heartbeat).start()
    threading.Thread(target=send_heartbeat).start()
    threading.Thread(target=multicast_listener).start()
    threading.Thread(target=accept_client_connections).start()

    try:
        while True:
            # Check periodically if the leader needs to be elected or updated.
            if not multicast_data.LEADER:
                notify_leader_election()
            else:
                notify_server_list_update()
            time.sleep(10)
    except KeyboardInterrupt:
        print("Server shutting down.")
        sys.exit()

if __name__ == '__main__':
    main()
