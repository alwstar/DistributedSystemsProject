# Import all relevant libraries
import socket
import threading
import time
import sys
import xml.etree.ElementTree as ET

# Constants
UDP_PORT = 5000
BUFFER_SIZE = 1024

# Default TCP Port
TCP_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 6000

# Global variables
clients = {}  # Dictionary to store client information (socket, address)
leader = None  # Current leader
running = True  # Server running state

# Shutdown event
shutdown_event = threading.Event()

# Heartbeat function
def send_heartbeat():
    HEARTBEAT_MESSAGE = ET.Element("heartbeat")
    while running:
        for client_socket in clients.values():
            try:
                client_socket.send(ET.tostring(HEARTBEAT_MESSAGE))
            except Exception as e:
                print(f"Failed to send heartbeat: {e}")
        time.sleep(60)

# Start the heartbeat function in a new thread
heartbeat_thread = threading.Thread(target=send_heartbeat)
heartbeat_thread.start()

# UDP Broadcast for dynamic discovery
def udp_broadcast():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while running:
            message = f"Server here:{TCP_PORT}".encode()
            udp_socket.sendto(message, ('<broadcast>', UDP_PORT))
            time.sleep(10)

# Function to initiate leader election
def start_election():
    global leader
    if clients:
        max_id = max(clients, key=lambda addr: addr[1])
        leader = max_id
        print(f"New leader elected: {max_id}")

# TCP Client handler
def client_handler(client_socket, addr):
    global clients, client_ring_order, leader
    while not shutdown_event.is_set():
        try:
            message = client_socket.recv(BUFFER_SIZE)
            if not message:
                break

            root = ET.fromstring(message)

            if root.tag == "election":
                handle_election_message(client_socket, addr, root)
            elif root.tag == "message":
                broadcast_message(addr, root.find("content").text)
            else:
                print(f"Received unknown message type from {addr}: {ET.tostring(root).decode()}")

        except socket.error as e:
            print(f"Socket error in client_handler for {addr}: {e}")
            break
        except Exception as e:
            print(f"Failed to handle client {addr}: {e}")
            break

    client_socket.close()
    print(f"Connection with {addr} closed")
    if addr in clients:
        del clients[addr]
        if addr in client_ring_order:
            client_ring_order.remove(addr)

        if addr == leader:
            print("Leader has disconnected. Starting a new election.")
            start_election()

def broadcast_message(sender_addr, msg_content):
    message = ET.Element("chatMessage")
    ET.SubElement(message, "senderIP").text = sender_addr[0]
    ET.SubElement(message, "senderPort").text = str(sender_addr[1])
    ET.SubElement(message, "content").text = msg_content

    for client_addr, client_socket in clients.items():
        try:
            client_socket.send(ET.tostring(message))
        except Exception as e:
            print(f"Error sending message to {client_addr}: {e}")

# Handle election messages
def handle_election_message(client_socket, addr, message):
    is_leader = message.find("isLeader").text.lower() == "true"
    if is_leader:
        announce_leader(addr)
    else:
        forward_election_message(addr, message)

# Additional global variable to store the order of clients in the ring
client_ring_order = []

def forward_election_message(sender_addr, message):
    global clients, client_ring_order
    sender_index = client_ring_order.index(sender_addr)
    next_client_index = (sender_index + 1) % len(client_ring_order)
    next_client_addr = client_ring_order[next_client_index]

    if next_client_addr in clients:
        next_client_socket = clients[next_client_addr]
        next_client_socket.send(ET.tostring(message))

# Announce the new leader
def announce_leader(leader_addr):
    global leader
    leader = leader_addr
    leader_announcement = ET.Element("leader")
    ET.SubElement(leader_announcement, "uid").text = str(leader_addr[1])

    for client_socket in clients.values():
        client_socket.send(ET.tostring(leader_announcement))

    print(f"Leader is {leader_addr}")

# Shut down the server
def shutdown_server(tcp_socket):
    global running
    running = False
    shutdown_event.set()

    client_addresses = list(clients.keys())

    for addr in client_addresses:
        try:
            clients[addr].close()
        except Exception as e:
            print(f"Error closing connection with {addr}: {e}")
        finally:
            if addr in clients:
                del clients[addr]

    tcp_socket.close()
    print("Server has been shut down.")

# List all connected clients
def list_connected_clients():
    if clients:
        print("Connected clients:")
        for addr in clients.keys():
            print(f"Client at {addr}")
    else:
        print("No clients connected.")

def main():
    global running, leader

    tcp_port = TCP_PORT

    if len(sys.argv) > 1:
        try:
            tcp_port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number. Using default port:", TCP_PORT)

    udp_thread = threading.Thread(target=udp_broadcast)
    udp_thread.start()

    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_socket.bind(('', TCP_PORT))
    tcp_socket.listen()
    print(f"TCP server listening on port {TCP_PORT}")

    def handle_connections(tcp_socket):
        global clients, client_ring_order, running

        while running:
            try:
                client_socket, addr = tcp_socket.accept()
                client_id = addr[1]

                clients[addr] = client_socket
                client_ring_order.append(addr)

                print(f"Connected to {addr}")

                threading.Thread(target=client_handler, args=(client_socket, addr)).start()

                if len(clients) == 1 or leader is None:
                    start_election()

            except ConnectionAbortedError:
                print("Server is shutting down, closing connection thread.")
                break
            except Exception as e:
                print(f"Error in connection handling: {e}")

        try:
            tcp_socket.close()
        except Exception as e:
            print(f"Error closing server socket: {e}")

    connection_thread = threading.Thread(target=handle_connections, args=(tcp_socket,))
    connection_thread.start()

    while running:
        cmd = input("Enter a command (1: exit, 2: list clients, 3: list current leader): ")
        if cmd == '1':
            shutdown_server(tcp_socket)
            break
        elif cmd == '2':
            list_connected_clients()
        elif cmd == '3':
            if leader:
                print(f"Current leader is: {leader}")
            else:
                print("No leader has been elected yet.")
        else:
            print("Invalid command.")

    connection_thread.join()
    udp_thread.join()

if __name__ == "__main__":
    main()