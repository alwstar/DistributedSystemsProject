# Import all relevant libraries
import socket
import threading
import time
import sys
import json

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
    HEARTBEAT_MESSAGE = b"HEARTBEAT"
    while running:
        for client_socket in clients.values():
            try:
                client_socket.send(HEARTBEAT_MESSAGE)
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
            message = f"Server here:{TCP_PORT}".encode()  # Includes the TCP port in the message
            udp_socket.sendto(message, ('<broadcast>', UDP_PORT))
            time.sleep(10)

# Function to initiate leader election
def start_election():
    global leader
    if clients:
        max_id = max(clients, key=lambda addr: addr[1])
        leader = max_id  # Store the client's address
        print(f"New leader elected: {max_id}")


# TCP Client handler
def client_handler(client_socket, addr):
    global clients, client_ring_order, leader
    while not shutdown_event.is_set():
        try:
            message = client_socket.recv(BUFFER_SIZE)
            if not message:
                break

            # Checks if the message is for election
            try:
                election_message = json.loads(message.decode())
                if 'uid' in election_message and 'isLeader' in election_message:
                    handle_election_message(client_socket, addr, election_message)
                    continue
            except json.JSONDecodeError:
                pass  # Not an election message, proceed with normal handling
        
            # Split the received message
            target_client_addr, sender_addr, message = message.decode().split(":", 2)
            # Forward the message to the target client
            forward_message(target_client_addr, message, sender_addr)

        except socket.error as e:
            print(f"Socket error in client_handler for {addr}: {e}")
            break
        except Exception as e:
            print(f"Failed to handle client {addr}: {e}")
            break

    # Remove the client from clients and client_ring_order upon disconnection
    client_socket.close()
    print(f"Connection with {addr} closed")
    if addr in clients:
        del clients[addr]
        if addr in client_ring_order:
            client_ring_order.remove(addr)

        if addr == leader:
            print("Leader has disconnected. Starting a new election.")
            start_election()

def forward_message(recipient_addr_str, msg_content, sender_addr):
    try:
        # Removes parentheses and split the address into IP and port
        recipient_addr_str = recipient_addr_str.strip("()")
        ip_port = recipient_addr_str.split(", ")
        
        if len(ip_port) != 2:
            raise ValueError("Invalid address format")

        recipient_ip = ip_port[0]
        recipient_port = int(ip_port[1])

        recipient_addr = (recipient_ip, recipient_port)

        if recipient_addr in clients:
            client_socket = clients[recipient_addr]
            forward_msg = f"From {sender_addr}: {msg_content}"
            client_socket.send(forward_msg.encode())
            print(f"Forwarded message from {sender_addr} to {recipient_addr}")
        else:
            print(f"Recipient {recipient_addr} not found. Message not sent.")
    except Exception as e:
        print(f"Error in forwarding message: {e}")

# Handle election messages
def handle_election_message(addr, message):
    global clients
    if message['isLeader']:
        announce_leader(addr)
    else:
        forward_election_message(addr, message)

# Additional global variable to store the order of clients in the ring
client_ring_order = []

def forward_election_message(sender_addr, message):
    global clients, client_ring_order
    # Find the next client in the ring
    sender_index = client_ring_order.index(sender_addr)
    next_client_index = (sender_index + 1) % len(client_ring_order)
    next_client_addr = client_ring_order[next_client_index]

    # Forward the election message to the next client
    if next_client_addr in clients:
        next_client_socket = clients[next_client_addr]
        next_client_socket.send(json.dumps(message).encode())

# Announce the new leader
def announce_leader(leader_addr):
    global leader
    leader = leader_addr  # Store the leader's address
    leader_announcement = json.dumps({"leader": leader_addr, "isLeader": True})

    # Broadcast the leader announcement to all clients
    for client_socket in clients.values():
        client_socket.send(leader_announcement.encode())

    print(f"Leader is {leader_addr}")

# Shut down the server
def shutdown_server(tcp_socket):
    global running
    running = False
    shutdown_event.set()  # Signal all threads to shut down

    # Create a list of client addresses
    client_addresses = list(clients.keys())

    # Iterate over the list of client addresses
    for addr in client_addresses:
        try:
            clients[addr].close()
        except Exception as e:
            print(f"Error closing connection with {addr}: {e}")
        finally:
            # Safely remove the client from the dictionary if it exists
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

    # Default TCP port
    tcp_port = TCP_PORT

    # Check for command-line argument for TCP port
    if len(sys.argv) > 1:
        try:
            tcp_port = int(sys.argv[1])
        except ValueError:
            print("Invalid port number. Using default port:", TCP_PORT)

    # UDP broadcast thread
    udp_thread = threading.Thread(target=udp_broadcast)
    udp_thread.start()

    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # New line to set SO_REUSEADDR
    tcp_socket.bind(('', TCP_PORT))
    tcp_socket.listen()
    print(f"TCP server listening on port {TCP_PORT}")

    # Handling new connections
    def handle_connections(tcp_socket):
        global clients, client_ring_order, running

        while running:
            try:
                client_socket, addr = tcp_socket.accept()
                # Using port number as a unique ID for simplicity
                client_id = addr[1]

                # Add the new client to the clients dictionary and the ring order
                clients[addr] = client_socket
                client_ring_order.append(addr)

                print(f"Connected to {addr}")

                # Start a separate thread for this client
                threading.Thread(target=client_handler, args=(client_socket, addr)).start()

                # Start election if this is the first client or if there's no leader
                if len(clients) == 1 or leader is None:
                    start_election()

            except ConnectionAbortedError:
                print("Server is shutting down, closing connection thread.")
                break
            except Exception as e:
                print(f"Error in connection handling: {e}")

        # Close the server socket if it's not already closed
        try:
            tcp_socket.close()
        except Exception as e:
            print(f"Error closing server socket: {e}")

    # Wait for the connection thread to finish
    connection_thread = threading.Thread(target=handle_connections, args=(tcp_socket,))
    connection_thread.start()

    # Command line interface for server control
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

    # Wait for threads to finish
    connection_thread.join()
    udp_thread.join()

if __name__ == "__main__":
    main()