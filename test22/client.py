import socket
import threading
import sys
import time
import xml.etree.ElementTree as ET

# Constants
SERVER_UDP_PORT = 5000
BUFFER_SIZE = 1024

# Global variables
shutdown_event = threading.Event()
my_id = None
current_chatroom = None

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

# Function to send messages to the server
def send_message_to_server(tcp_socket, message_type, **kwargs):
    try:
        message = create_xml_message(message_type, **kwargs)
        tcp_socket.send(message)
    except ConnectionError:
        print("Lost connection to the server.")
        tcp_socket.close()

# Function to handle incoming messages from the server
def receive_messages(tcp_socket):
    global my_id, current_chatroom
    while not shutdown_event.is_set():
        try:
            message = tcp_socket.recv(BUFFER_SIZE)
            if not message:
                break

            message_type, data = parse_xml_message(message)

            if message_type == "leader_announcement":
                print(f"New leader is {data['leader_ip']}:{data['leader_port']}")
            elif message_type == "election_response":
                if int(data['leader_id']) > my_id:
                    print(f"A higher ID client ({data['leader_id']}) is already in the election.")
                else:
                    send_message_to_server(tcp_socket, "election", id=my_id)
            elif message_type == "chatroom_announcement":
                print(f"Client {data['client_ip']}:{data['client_port']} has {data['action']} chatroom {data['chatroom']}")
            elif message_type == "chatroom_message":
                print(f"[{data['chatroom']}] {data['sender_ip']}:{data['sender_port']}: {data['content']}")
            else:
                print(f"Received unknown message type: {message_type}")

        except Exception as e:
            print(f"Error receiving message: {e}")
            break

    if not shutdown_event.is_set():
        print("Lost connection to the server. Attempting to reconnect...")
        reconnect()

# Function to reconnect to the server
def reconnect():
    global tcp_socket
    while not shutdown_event.is_set():
        try:
            server_ip, server_tcp_port = discover_server()
            new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            new_socket.connect((server_ip, server_tcp_port))
            tcp_socket = new_socket
            print("Reconnected to the server.")
            threading.Thread(target=receive_messages, args=(tcp_socket,)).start()
            if current_chatroom:
                send_message_to_server(tcp_socket, "chatroom", action="join", chatroom=current_chatroom)
            return
        except Exception as e:
            print(f"Failed to reconnect: {e}")
            time.sleep(5)

# Main function to start the client
def main():
    global my_id, tcp_socket, current_chatroom

    try:
        server_ip, server_tcp_port = discover_server()
        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((server_ip, server_tcp_port))
        print("Connected to the server.")

        my_id = tcp_socket.getsockname()[1]
        print(f"My ID is {my_id}")

        threading.Thread(target=receive_messages, args=(tcp_socket,)).start()

        while True:
            print("\nMenu:")
            print("1. Join a chatroom")
            print("2. Leave current chatroom")
            print("3. Send a message to current chatroom")
            print("4. Initiate leader election")
            print("5. Shut down client")
            choice = input("Enter your choice (1-5): ")

            if choice == '1':
                chatroom = input("Enter chatroom name: ")
                current_chatroom = chatroom
                send_message_to_server(tcp_socket, "chatroom", action="join", chatroom=chatroom)
            elif choice == '2':
                if current_chatroom:
                    send_message_to_server(tcp_socket, "chatroom", action="leave", chatroom=current_chatroom)
                    current_chatroom = None
                else:
                    print("You are not in any chatroom.")
            elif choice == '3':
                if current_chatroom:
                    message = input("Enter your message: ")
                    send_message_to_server(tcp_socket, "chatroom", action="message", chatroom=current_chatroom, content=message)
                else:
                    print("You are not in any chatroom.")
            elif choice == '4':
                send_message_to_server(tcp_socket, "election", id=my_id)
            elif choice == '5':
                print("Shutting down client...")
                shutdown_event.set()
                tcp_socket.close()
                break
            else:
                print("Invalid choice. Please try again.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()