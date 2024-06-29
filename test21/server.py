import socket
import threading
import time
import sys
import json

# Constants
UDP_PORT = 5000
TCP_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 6000
BUFFER_SIZE = 1024
HEARTBEAT_INTERVAL = 5
ELECTION_TIMEOUT = 10

# Global variables
server_id = f"{socket.gethostbyname(socket.gethostname())}:{TCP_PORT}"
servers = {}  # {server_id: (ip, port)}
clients = {}  # {client_addr: client_socket}
leader = None
is_leader = False
running = True
shutdown_event = threading.Event()

def udp_broadcast():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while running:
            message = json.dumps({"type": "SERVER_ANNOUNCE", "id": server_id, "tcp_port": TCP_PORT})
            udp_socket.sendto(message.encode(), ('<broadcast>', UDP_PORT))
            time.sleep(10)

def udp_listener():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udp_socket.bind(('', UDP_PORT))
        while running:
            try:
                message, addr = udp_socket.recvfrom(BUFFER_SIZE)
                message_data = json.loads(message.decode())
                if message_data['type'] == 'SERVER_ANNOUNCE':
                    if message_data['id'] not in servers and message_data['id'] != server_id:
                        print(f"Discovered new server: {message_data['id']}")
                        servers[message_data['id']] = (addr[0], message_data['tcp_port'])
                        connect_to_server(message_data['id'], addr[0], message_data['tcp_port'])
            except Exception as e:
                print(f"Error in UDP listener: {e}")

def connect_to_server(server_id, ip, port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, port))
            s.send(json.dumps({"type": "SERVER", "id": server_id}).encode())
            threading.Thread(target=handle_server_message, args=(s,)).start()
    except Exception as e:
        print(f"Failed to connect to server {server_id}: {e}")

def client_handler(client_socket, addr):
    global clients
    while not shutdown_event.is_set():
        try:
            message = client_socket.recv(BUFFER_SIZE)
            if not message:
                break

            message_data = json.loads(message.decode())
            if message_data['type'] == 'CLIENT_MESSAGE':
                forward_message(message_data['target'], message_data['content'], addr)
            elif message_data['type'] == 'HEARTBEAT_RESPONSE':
                # Handle client heartbeat response
                pass

        except Exception as e:
            print(f"Error handling client {addr}: {e}")
            break

    client_socket.close()
    print(f"Connection with client {addr} closed")
    if addr in clients:
        del clients[addr]

def forward_message(recipient_addr, msg_content, sender_addr):
    if recipient_addr in clients:
        client_socket = clients[recipient_addr]
        forward_msg = json.dumps({
            "type": "FORWARDED_MESSAGE",
            "sender": str(sender_addr),
            "content": msg_content
        })
        client_socket.send(forward_msg.encode())
        print(f"Forwarded message from {sender_addr} to {recipient_addr}")
    else:
        print(f"Recipient {recipient_addr} not found. Message not sent.")

def send_heartbeat():
    global is_leader
    while running:
        if is_leader:
            heartbeat_msg = json.dumps({"type": "HEARTBEAT", "leader": server_id})
            for server in servers.values():
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.connect(server)
                        s.send(heartbeat_msg.encode())
                except Exception as e:
                    print(f"Failed to send heartbeat to server {server}: {e}")
            
            for client in clients.values():
                try:
                    client.send(heartbeat_msg.encode())
                except Exception as e:
                    print(f"Failed to send heartbeat to client: {e}")
        time.sleep(HEARTBEAT_INTERVAL)

def start_election():
    global leader, is_leader
    print("Starting election")
    higher_servers = {id: server for id, server in servers.items() if id > server_id}
    
    if not higher_servers:
        become_leader()
        return

    election_msg = json.dumps({"type": "ELECTION", "id": server_id})
    for server in higher_servers.values():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(server)
                s.send(election_msg.encode())
                s.settimeout(ELECTION_TIMEOUT)
                response = s.recv(BUFFER_SIZE)
                if response:
                    print(f"Received response from higher server {server}")
                    return
        except socket.timeout:
            print(f"No response from server {server}")
        except Exception as e:
            print(f"Error communicating with server {server}: {e}")
    
    become_leader()

def become_leader():
    global leader, is_leader
    leader = server_id
    is_leader = True
    print(f"Becoming leader: {server_id}")
    announce_leader()

def announce_leader():
    coordinator_msg = json.dumps({"type": "COORDINATOR", "leader": server_id})
    for server in servers.values():
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(server)
                s.send(coordinator_msg.encode())
        except Exception as e:
            print(f"Failed to send coordinator message to server {server}: {e}")
    
    for client in clients.values():
        try:
            client.send(coordinator_msg.encode())
        except Exception as e:
            print(f"Failed to send coordinator message to client: {e}")

def handle_election_message(message, addr):
    if message['id'] < server_id:
        response = json.dumps({"type": "ELECTION_RESPONSE", "id": server_id})
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(addr)
            s.send(response.encode())
        start_election()
    else:
        print(f"Received election message from higher server {message['id']}")

def handle_coordinator_message(message, addr):
    global leader, is_leader
    leader = message['leader']
    is_leader = (leader == server_id)
    print(f"New leader is: {leader}")

def sync_state():
    if is_leader:
        # In this simple implementation, we're just collecting client information
        # In a more complex system, you'd sync more state information
        for server in servers.values():
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect(server)
                    s.send(json.dumps({"type": "STATE_REQUEST"}).encode())
                    response = json.loads(s.recv(BUFFER_SIZE).decode())
                    if response['type'] == 'STATE_RESPONSE':
                        for client_addr in response['clients']:
                            if client_addr not in clients:
                                clients[client_addr] = None  # We don't have the actual socket, just tracking the address
            except Exception as e:
                print(f"Failed to sync state with server {server}: {e}")

def handle_server_message(server_socket):
    while running:
        try:
            message = server_socket.recv(BUFFER_SIZE)
            if not message:
                break

            message_data = json.loads(message.decode())
            if message_data['type'] == 'ELECTION':
                handle_election_message(message_data, server_socket.getpeername())
            elif message_data['type'] == 'COORDINATOR':
                handle_coordinator_message(message_data, server_socket.getpeername())
            elif message_data['type'] == 'HEARTBEAT':
                # Reset heartbeat timer
                pass
            elif message_data['type'] == 'STATE_REQUEST':
                response = json.dumps({
                    "type": "STATE_RESPONSE",
                    "clients": list(clients.keys())
                })
                server_socket.send(response.encode())

        except Exception as e:
            print(f"Error handling server message: {e}")
            break

    server_socket.close()

def main():
    global running, leader

    udp_broadcast_thread = threading.Thread(target=udp_broadcast)
    udp_broadcast_thread.start()

    udp_listener_thread = threading.Thread(target=udp_listener)
    udp_listener_thread.start()

    heartbeat_thread = threading.Thread(target=send_heartbeat)
    heartbeat_thread.start()

    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_socket.bind(('', TCP_PORT))
    tcp_socket.listen()
    print(f"TCP server listening on port {TCP_PORT}")

    def handle_connections():
        while running:
            try:
                client_socket, addr = tcp_socket.accept()
                print(f"New connection from {addr}")
                
                identity = json.loads(client_socket.recv(BUFFER_SIZE).decode())
                
                if identity['type'] == 'SERVER':
                    servers[identity['id']] = addr
                    threading.Thread(target=handle_server_message, args=(client_socket,)).start()
                elif identity['type'] == 'CLIENT':
                    clients[addr] = client_socket
                    threading.Thread(target=client_handler, args=(client_socket, addr)).start()

                if leader is None:
                    start_election()

            except Exception as e:
                print(f"Error in connection handling: {e}")

    connection_thread = threading.Thread(target=handle_connections)
    connection_thread.start()

    while running:
        cmd = input("Enter a command (exit, list_clients, list_servers, leader): ")
        if cmd == 'exit':
            running = False
            shutdown_event.set()
            tcp_socket.close()
            break
        elif cmd == 'list_clients':
            print("Connected clients:", list(clients.keys()))
        elif cmd == 'list_servers':
            print("Known servers:", list(servers.keys()))
        elif cmd == 'leader':
            print(f"Current leader: {leader}")
        else:
            print("Invalid command.")

    udp_broadcast_thread.join()
    udp_listener_thread.join()
    heartbeat_thread.join()
    connection_thread.join()

if __name__ == "__main__":
    main()