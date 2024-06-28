# Import all relevant libraries
import socket
import threading
import sys
import time
import json

# Constants
SERVER_UDP_PORT = 5000
SERVER_TCP_PORT = 6000
BUFFER_SIZE = 1024

# Global shutdown event
shutdown_event = threading.Event()

# Discover the server using UDP broadcast
def discover_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.bind(('', SERVER_UDP_PORT))

        while True:
            message, server_addr = udp_socket.recvfrom(BUFFER_SIZE)
            # Extracts the IP address from server_addr and the port from the message
            server_ip = server_addr[0]
            _, server_tcp_port = message.decode().split(':')
            print(f"Discovered server at {server_ip} on port {server_tcp_port}")
            return server_ip, int(server_tcp_port)

# Function to send messages to another client via the server
def send_message_to_client(tcp_socket, target_client_addr, sender_addr, message):
    try:
        # Include sender's address in the message
        data = f"{target_client_addr}:{sender_addr}:{message}".encode()
        tcp_socket.send(data)
    except ConnectionError:
        print("Lost connection to the server.")
        tcp_socket.close()

# Function to send election messages
def send_election_message(tcp_socket, message):
    try:
        tcp_socket.send(json.dumps(message).encode())
    except Exception as e:
        print(f"Error sending election message: {e}")

# Function to handle incoming election messages
def handle_election_message(tcp_socket, election_message):
    global my_uid
    if election_message['uid'] < my_uid:
        # If received UID is less than my UID, start a new election with my UID
        send_election_message(tcp_socket, {"uid": my_uid, "isLeader": False})
    elif election_message['uid'] > my_uid:
        # If received UID is greater, forward the message
        send_election_message(tcp_socket, election_message)
    else:
        # If received UID is equal to my UID, I am the leader
        print("I am the leader")
        send_election_message(tcp_socket, {"uid": my_uid, "isLeader": True})

# Function to handle incoming messages from the server
def receive_messages(tcp_socket):
    global my_uid  # Assuming each client has a unique identifier (my_uid)
    while not shutdown_event.is_set():
        try:
            message = tcp_socket.recv(BUFFER_SIZE)
            if not message:
                break

            # Check if the message is a leader announcement
            try:
                leader_message = json.loads(message.decode())
                if 'leader' in leader_message and leader_message['isLeader']:
                    if leader_message['leader'] == my_uid:
                        print("I am the new leader")
                    else:
                        print(f"New leader is {leader_message['leader']}")
                    continue
            except json.JSONDecodeError:
                pass  # Not a leader message, proceed with normal handling

            print(f"Received message: {message.decode()}")

        except (ConnectionError, OSError) as e:
            print("Socket error or lost connection:", e)
            break

    if not shutdown_event.is_set():
        rediscover_and_connect()

# Function to rediscover the server and reconnect
def rediscover_and_connect():
    print("Attempting to rediscover available servers...")
    for attempt in range(5):  # Retry up to 5 times
        try:
            server_ip, server_tcp_port = discover_server()
            print("Trying to connect to server IP:", server_ip, "Port:", server_tcp_port)  # Debug print
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.connect((server_ip, server_tcp_port))
            print("Reconnected to a new server.")

            # Restart the thread to listen for messages from the new server
            threading.Thread(target=receive_messages, args=(tcp_socket,)).start()
            return
        except Exception as e:
            print(f"Failed to connect to a new server: {e}")
            time.sleep(2)  # Wait for 2 seconds before retrying

    print("Unable to reconnect to a new server after several attempts.")

my_uid = None  # This will store the client's UID

# Main function to start the client
def main():
    global my_uid

    try:
        server_ip, server_tcp_port = discover_server()
        print("Discovered server IP:", server_ip, "Port:", server_tcp_port)  # Debug print

        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((server_ip, server_tcp_port))
        print("Connected to the server.")

        # Start a thread to listen for messages from the server
        threading.Thread(target=receive_messages, args=(tcp_socket,)).start()

        # Get the client's UID from the server
        my_uid = tcp_socket.getsockname()[1]
        print(f"My UID is {my_uid}")

        # User interaction loop
        while True:
            print("\nMenu:")
            print("1. Send a message")
            print("2. Shut down client")
            choice = input("Enter your choice (1-2): ")

            # Send a message to another client
            if choice == '1':
                message = input("Enter your message: ")
                target_client_addr = input("Enter the target client's address: ")
                sender_addr = str(tcp_socket.getsockname())  # Get the client's own address
                send_message_to_client(tcp_socket, target_client_addr, sender_addr, message)
            # Shut down the client
            elif choice == '2':
                print("Shutting down client...")
                shutdown_event.set()  # Signal the receive_messages thread to stop
                tcp_socket.close()
                print("Client shut down.")
                break
            else:
                print("Invalid choice. Please try again.")
        
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()
