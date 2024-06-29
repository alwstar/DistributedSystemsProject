import socket
import threading
import time
import sys
import xml.etree.ElementTree as ET

# Constants
UDP_PORT = 5000
BUFFER_SIZE = 1024
TCP_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 6000

# Global variables
clients = {}  # Dictionary to store client information (socket, address)
leader = None  # Current leader
running = True  # Server running state
chatrooms = {}  # Dictionary to store chatrooms and their members

# Shutdown event
shutdown_event = threading.Event()

def start_election():
    global leader
    if clients:
        max_id = max(clients, key=lambda addr: addr[1])
        leader = max_id
        announce_leader(leader)
    else:
        leader = None
        print("No clients connected. Cannot start election.")

# UDP Broadcast for dynamic discovery
def udp_broadcast():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while running:
            message = f"Server here:{TCP_PORT}".encode()
            udp_socket.sendto(message, ('<broadcast>', UDP_PORT))
            time.sleep(10)

# Function to create XML message
def create_xml_message(message_type, **kwargs):
    root = ET.Element("message")
    ET.SubElement(root, "type").text = message_type
    for key, value in kwargs.items():
        ET.SubElement(root, key).text = str(value)
    return ET.tostring(root)

# Function to parse XML message
def parse_xml_message(xml_string):
    root = ET.fromstring(xml_string)
    message_type = root.find("type").text
    data = {child.tag: child.text for child in root if child.tag != "type"}
    return message_type, data

# TCP Client handler
def client_handler(client_socket, addr):
    global clients, leader
    while not shutdown_event.is_set():
        try:
            message = client_socket.recv(BUFFER_SIZE)
            if not message:
                break

            message_type, data = parse_xml_message(message)

            if message_type == "election":
                handle_election_message(client_socket, addr, data)
            elif message_type == "chatroom":
                handle_chatroom_message(client_socket, addr, data)
            else:
                print(f"Unknown message type: {message_type}")

        except Exception as e:
            print(f"Error handling client {addr}: {e}")
            break

    client_socket.close()
    print(f"Connection with {addr} closed")
    if addr in clients:
        del clients[addr]
        for chatroom in chatrooms.values():
            if addr in chatroom:
                chatroom.remove(addr)
        if addr == leader:
            print("Leader has disconnected. Starting a new election.")
            start_election()


# Handle election messages (LCR algorithm)
def handle_election_message(client_socket, addr, data):
    global leader
    sender_id = data['mid']
    is_leader = data['isLeader'] == 'true'

    if is_leader:
        leader = (addr[0], int(sender_id))
        announce_leader(leader)
    else:
        # Forward the message to the next client in the ring
        next_client = get_next_client(addr)
        if next_client:
            clients[next_client].send(create_xml_message("election", mid=sender_id, isLeader="false"))

# Get the next client in the ring
def get_next_client(current_addr):
    client_list = list(clients.keys())
    if current_addr in client_list:
        current_index = client_list.index(current_addr)
        next_index = (current_index + 1) % len(client_list)
        return client_list[next_index]
    return None

# Announce the new leader
def announce_leader(leader_addr):
    leader_announcement = create_xml_message("leader_announcement", leader_ip=leader_addr[0], leader_port=leader_addr[1])
    for client_socket in clients.values():
        client_socket.send(leader_announcement)
    print(f"Leader is {leader_addr}")

# Handle chatroom messages
def handle_chatroom_message(client_socket, addr, data):
    action = data['action']
    chatroom = data['chatroom']

    if action == "join":
        if chatroom not in chatrooms:
            chatrooms[chatroom] = set()
        chatrooms[chatroom].add(addr)
        announce_client_joined(chatroom, addr)
    elif action == "leave":
        if chatroom in chatrooms and addr in chatrooms[chatroom]:
            chatrooms[chatroom].remove(addr)
            announce_client_left(chatroom, addr)
    elif action == "message":
        if chatroom in chatrooms and addr in chatrooms[chatroom]:
            broadcast_chatroom_message(chatroom, addr, data['content'])

# Announce client joined chatroom
def announce_client_joined(chatroom, addr):
    announcement = create_xml_message("chatroom_announcement", action="joined", chatroom=chatroom, client_ip=addr[0], client_port=addr[1])
    for client_addr in chatrooms[chatroom]:
        if client_addr in clients:
            clients[client_addr].send(announcement)

# Announce client left chatroom
def announce_client_left(chatroom, addr):
    announcement = create_xml_message("chatroom_announcement", action="left", chatroom=chatroom, client_ip=addr[0], client_port=addr[1])
    for client_addr in chatrooms[chatroom]:
        if client_addr in clients:
            clients[client_addr].send(announcement)

# Broadcast message to chatroom
def broadcast_chatroom_message(chatroom, sender_addr, content):
    message = create_xml_message("chatroom_message", chatroom=chatroom, sender_ip=sender_addr[0], sender_port=sender_addr[1], content=content)
    for client_addr in chatrooms[chatroom]:
        if client_addr in clients:
            clients[client_addr].send(message)

# Shut down the server
def shutdown_server(tcp_socket):
    global running
    running = False
    shutdown_event.set()

    for client_socket in clients.values():
        try:
            client_socket.close()
        except Exception as e:
            print(f"Error closing client connection: {e}")

    clients.clear()
    chatrooms.clear()
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
    tcp_socket.bind(('', tcp_port))
    tcp_socket.listen()
    print(f"TCP server listening on port {tcp_port}")

    def handle_connections(tcp_socket):
        global clients, running

        while running:
            try:
                client_socket, addr = tcp_socket.accept()
                clients[addr] = client_socket
                print(f"Connected to {addr}")
                threading.Thread(target=client_handler, args=(client_socket, addr)).start()

                if leader is None:
                    start_election()

            except Exception as e:
                print(f"Error in connection handling: {e}")

        tcp_socket.close()

    connection_thread = threading.Thread(target=handle_connections, args=(tcp_socket,))
    connection_thread.start()

    while running:
        cmd = input("\nSelect an option\n1: Show current leader\n2: Show clients\n3: Shut down server\n")
        if cmd == '3':
            shutdown_server(tcp_socket)
            break
        elif cmd == '2':
            list_connected_clients()
        elif cmd == '1':
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