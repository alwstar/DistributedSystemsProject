import socket
import threading
import sys
import time
import json
import logging

class NetworkSettings:
    UDP_DISCOVERY_PORT = 5000
    TCP_COMM_PORT = 6000
    DATA_BUFFER_SIZE = 1024

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

shutdown_event = threading.Event()

def discover_server():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.bind(('', NetworkSettings.UDP_DISCOVERY_PORT))

        while True:
            data_packet, server_addr = udp_socket.recvfrom(NetworkSettings.DATA_BUFFER_SIZE)
            server_ip = server_addr[0]
            _, server_tcp_port = data_packet.decode().split(':')
            logging.info(f"Discovered server at {server_ip} on port {server_tcp_port}")
            return server_ip, int(server_tcp_port)

def send_message_to_client(tcp_socket, target_client_endpoint, sender_endpoint, msg_content):
    try:
        data = f"{target_client_endpoint}:{sender_endpoint}:{msg_content}".encode()
        tcp_socket.send(data)
    except ConnectionError:
        logging.error("Lost connection to the server.")
        tcp_socket.close()

def send_election_message(tcp_socket, message):
    try:
        tcp_socket.send(json.dumps(message).encode())
    except Exception as e:
        logging.error(f"Error sending election message: {e}")

def handle_election_message(tcp_socket, election_message):
    global my_uid
    if election_message['uid'] < my_uid:
        send_election_message(tcp_socket, {"uid": my_uid, "isLeader": False})
    elif election_message['uid'] > my_uid:
        send_election_message(tcp_socket, election_message)
    else:
        logging.info("I am the leader")
        send_election_message(tcp_socket, {"uid": my_uid, "isLeader": True})

def receive_messages(tcp_socket):
    global my_uid
    while not shutdown_event.is_set():
        try:
            msg_content = tcp_socket.recv(NetworkSettings.DATA_BUFFER_SIZE)
            if not msg_content:
                break

            try:
                leader_message = json.loads(msg_content.decode())
                if 'leader' in leader_message and leader_message['isLeader']:
                    logging.info(f"I am the new leader" if leader_message['leader'] == my_uid else f"New leader is {leader_message['leader']}")
                    continue
            except json.JSONDecodeError:
                pass

            logging.info(f"Received message: {msg_content.decode()}")

        except (ConnectionError, OSError) as e:
            logging.error(f"Socket error or lost connection: {e}")
            break

    if not shutdown_event.is_set():
        rediscover_and_connect()

def rediscover_and_connect():
    logging.info("Attempting to rediscover available servers...")
    for attempt in range(5):
        try:
            server_ip, server_tcp_port = discover_server()
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.connect((server_ip, server_tcp_port))
            logging.info("Reconnected to a new server.")

            threading.Thread(target=receive_messages, args=(tcp_socket,)).start()
            return
        except Exception as e:
            logging.error(f"Failed to connect to a new server: {e}")
            time.sleep(2)

    logging.error("Unable to reconnect to a new server after several attempts.")

my_uid = None

def main():
    global my_uid

    try:
        server_ip, server_tcp_port = discover_server()

        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.connect((server_ip, server_tcp_port))
        logging.info("Connected to the server.")

        threading.Thread(target=receive_messages, args=(tcp_socket,)).start()

        my_uid = tcp_socket.getsockname()[1]

        while True:
            logging.info("\nMenu:\n1. Send a message\n2. Shut down client")
            choice = input("Enter your choice (1-2): ")

            if choice == '1':
                msg_content = input("Enter your message: ")
                target_client_endpoint = input("Enter the target client's address: ")
                sender_endpoint = str(tcp_socket.getsockname())
                send_message_to_client(tcp_socket, target_client_endpoint, sender_endpoint, msg_content)
            elif choice == '2':
                logging.info("Shutting down client...")
                shutdown_event.set()
                tcp_socket.close()
                logging.info("Client shut down.")
                break
            else:
                logging.error("Invalid choice. Please try again.")
        
    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
