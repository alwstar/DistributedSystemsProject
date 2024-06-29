import socket
import threading
import time
import sys
import json
import logging

class NetworkSettings:
    UDP_PORT = 5000
    DATA_BUFFER_SIZE = 1024
    TCP_PORT = 6000  # Default TCP Port

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

clients = {}  # Dictionary to store client information (socket, address)
leader = None  # Current leader
running = True  # Server running state
shutdown_event = threading.Event()

def send_heartbeat():
    while running:
        for client_socket in clients.values():
            try:
                client_socket.send(b"HEARTBEAT")
            except Exception as e:
                logging.error(f"Failed to send heartbeat: {e}")
        time.sleep(60)

heartbeat_thread = threading.Thread(target=send_heartbeat)
heartbeat_thread.start()

def udp_broadcast():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while running:
            message = f"Server here:{NetworkSettings.TCP_PORT}".encode()
            udp_socket.sendto(message, ('<broadcast>', NetworkSettings.UDP_PORT))
            time.sleep(10)

def start_election():
    global leader
    if clients:
        max_id = max(clients, key=lambda addr: addr[1])
        leader = max_id
        logging.info(f"New leader elected: {max_id}")

def client_handler(client_socket, addr):
    global clients, leader
    while not shutdown_event.is_set():
        try:
            message = client_socket.recv(NetworkSettings.DATA_BUFFER_SIZE)
            if not message:
                break

            try:
                election_message = json.loads(message.decode())
                if 'uid' in election_message and 'isLeader' in election_message:
                    handle_election_message(client_socket, addr, election_message)
                    continue
            except json.JSONDecodeError:
                pass

            target_client_endpoint, sender_endpoint, msg_content = message.decode().split(":", 2)
            forward_message(target_client_endpoint, msg_content, sender_endpoint)

        except socket.error as e:
            logging.error(f"Socket error in client_handler for {addr}: {e}")
            break
        except Exception as e:
            logging.error(f"Failed to handle client {addr}: {e}")
            break

    client_socket.close()
    logging.info(f"Connection with {addr} closed")
    if addr in clients:
        del clients[addr]
        if addr == leader:
            logging.info("Leader has disconnected. Starting a new election.")
            start_election()

def forward_message(recipient_addr_str, msg_content, sender_addr):
    try:
        recipient_addr = tuple(map(int, recipient_addr_str.strip("()").split(", ")))
        if recipient_addr in clients:
            client_socket = clients[recipient_addr]
            forward_msg = f"From {sender_addr}: {msg_content}"
            client_socket.send(forward_msg.encode())
            logging.info(f"Forwarded message from {sender_addr} to {recipient_addr}")
        else:
            logging.error(f"Recipient {recipient_addr} not found. Message not sent.")
    except Exception as e:
        logging.error(f"Error in forwarding message: {e}")

def handle_election_message(client_socket, addr, message):
    global leader
    if message['isLeader']:
        announce_leader(addr)
    else:
        forward_election_message(addr, message)

def forward_election_message(sender_addr, message):
    global clients
    next_client_addr = min((addr for addr in clients if addr > sender_addr), default=None)
    if next_client_addr:
        clients[next_client_addr].send(json.dumps(message).encode())

def announce_leader(leader_addr):
    global leader
    leader = leader_addr
    leader_announcement = json.dumps({"leader": leader_addr, "isLeader": True})
    for client_socket in clients.values():
        client_socket.send(leader_announcement.encode())
    logging.info(f"Leader is {leader_addr}")

def shutdown_server(tcp_socket):
    global running
    running = False
    shutdown_event.set()
    for client_socket in clients.values():
        client_socket.close()
    tcp_socket.close()
    logging.info("Server has been shut down.")

def list_connected_clients():
    if clients:
        logging.info("Connected clients:")
        for addr in clients:
            logging.info(f"Client at {addr}")
    else:
        logging.error("No clients connected.")

def main():
    global running, leader
    tcp_port = NetworkSettings.TCP_PORT
    if len(sys.argv) > 1:
        try:
            tcp_port = int(sys.argv[1])
        except ValueError:
            logging.error("Invalid port number. Using default port.")
    udp_thread = threading.Thread(target=udp_broadcast)
    udp_thread.start()
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.bind(('', tcp_port))
    tcp_socket.listen()
    logging.info(f"TCP server listening on port {tcp_port}")

    while running:
        try:
            client_socket, addr = tcp_socket.accept()
            clients[addr] = client_socket
            logging.info(f"Connected to {addr}")
            threading.Thread(target=client_handler, args=(client_socket, addr)).start()
            if len(clients) == 1 or leader is None:
                start_election()
        except ConnectionAbortedError:
            logging.error("Server is shutting down, closing connection thread.")
            break
        except Exception as e:
            logging.error(f"Error in connection handling: {e}")
    tcp_socket.close()

if __name__ == "__main__":
    main()
