# Import all relevant libraries
import socket
import threading
import sys
import time
import xml.etree.ElementTree as ET

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
            server_ip = server_addr[0]
            _, server_tcp_port = message.decode().split(':')
            print(f"Discovered server at {server_ip} on port {server_tcp_port}")
            return server_ip, int(server_tcp_port)

# Function to send messages to the chat room
def send_message_to_chat_room(tcp_socket, message):
    try:
        xml_message = ET.Element("message")
        ET.SubElement(xml_message, "content").text = message
        data = ET.tostring(xml_message)
        tcp_socket.send(data)
    except ConnectionError:
        print("Lost connection to the server.")
        tcp_socket.close()

# Function to send election messages
def send_election_message(tcp_socket, uid, is_leader):
    try:
        xml_message = ET.Element("election")
        ET.SubElement(xml_message, "uid").text = str(uid)
        ET.SubElement(xml_message, "isLeader").text = str(is_leader).lower()
        data = ET.tostring(xml_message)
        tcp_socket.send(data)
    except Exception as e:
        print(f"Error sending election message: {e}")

# Function to handle incoming election messages
def handle_election_message(tcp_socket, election_message):
    global my_uid
    received_uid = int(election_message.find("uid").text)
    is_leader = election_message.find("isLeader").text.lower() == "true"

    if received_uid < my_uid:
        send_election_message(tcp_socket, my_uid, False)
    elif received_uid > my_uid:
        send_election_message(tcp_socket, received_uid, False)
    else:
        print("I am the leader")
        send_election_message(tcp_socket, my_uid, True)

# Function to handle incoming messages from the server
def receive_messages(tcp_socket):
    global my_uid
    while not shutdown_event.is_set():
        try:
            message = tcp_socket.recv(BUFFER_SIZE)
            if not message:
                break

            root = ET.fromstring(message)

            if root.tag == "leader":
                leader_uid = int(root.find("uid").text)
                if leader_uid == my_uid:
                    print("I am the new leader")
                else:
                    print(f"New leader is {leader_uid}")
            elif root.tag == "chatMessage":
                sender_ip = root.find("senderIP").text
                sender_port = root.find("senderPort").text
                content = root.find("content").text
                print(f"Message from {sender_ip}:{sender_port}: {content}")
            else:
                print(f"Received message: {ET.tostring(root).decode()}")

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
            print("Trying to connect to server IP:", server_ip, "Port:", server_tcp_port)
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.connect((server_ip, server_tcp_port))
            print("Reconnected to a new server.")

            threading.Thread(target=receive_messages, args=(tcp_socket,)).start()
            return tcp_socket
        except Exception as e:
            print(f"Failed to connect to a new server: {e}")
            time.sleep(2)

    print("Unable to reconnect to a new server after several attempts.")
    return None

my_uid = None  # This will store the client's UID

# Main function to start the client
def main():
    global my_uid

    try:
        server_ip, server_tcp_port = discover_server()
        print("Discovered server IP:", server_ip, "Port:", server_tcp_port)

        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((server_ip, server_tcp_port))
        print("Connected to the server.")

        threading.Thread(target=receive_messages, args=(tcp_socket,)).start()

        my_uid = tcp_socket.getsockname()[1]
        print(f"My UID is {my_uid}")

        while True:
            print("\nMenu:")
            print("1. Send a message to chat room")
            print("2. Shut down client")
            choice = input("Enter your choice (1-2): ")

            if choice == '1':
                message = input("Enter your message: ")
                send_message_to_chat_room(tcp_socket, message)
            elif choice == '2':
                print("Shutting down client...")
                shutdown_event.set()
                tcp_socket.close()
                print("Client shut down.")
                break
            else:
                print("Invalid choice. Please try again.")
        
    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()