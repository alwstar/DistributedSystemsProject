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

class Server:
    def __init__(self):
        self.id = f"{socket.gethostbyname(socket.gethostname())}:{TCP_PORT}"
        self.servers = {}  # {server_id: (ip, port, socket)}
        self.clients = {}  # {client_addr: client_socket}
        self.leader = None
        self.is_leader = False
        self.running = True
        self.shutdown_event = threading.Event()
        self.last_heartbeat = time.time()
        self.heartbeat_timeout = 15  # seconds
        
        # Start an election when the server starts
        threading.Thread(target=self.start_election).start()

    def broadcast_server_info(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            while self.running:
                try:
                    message = json.dumps({
                        "type": "SERVER_ANNOUNCE",
                        "id": self.id,
                        "tcp_port": TCP_PORT,
                        "leader": self.leader
                    })
                    udp_socket.sendto(message.encode(), ('<broadcast>', UDP_PORT))
                    time.sleep(5)  # Broadcast every 5 seconds
                except Exception as e:
                    print(f"Error in server broadcast: {e}")

    def udp_listener(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            udp_socket.bind(('', UDP_PORT))
            print(f"UDP listener started on port {UDP_PORT}")
            while self.running:
                try:
                    message, addr = udp_socket.recvfrom(BUFFER_SIZE)
                    message_data = json.loads(message.decode())
                    if message_data['type'] == 'SERVER_ANNOUNCE':
                        if message_data['id'] not in self.servers and message_data['id'] != self.id:
                            print(f"Discovered new server: {message_data['id']}")
                            self.connect_to_server(message_data['id'], addr[0], message_data['tcp_port'])
                except Exception as e:
                    print(f"Error in UDP listener: {e}")

    def connect_to_server(self, new_server_id, ip, port):
        if new_server_id in self.servers:
            return  # Already connected to this server

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((ip, int(port)))
            s.send(json.dumps({"type": "SERVER", "id": self.id}).encode())
            self.servers[new_server_id] = (ip, int(port), s)
            print(f"Connected to server: {new_server_id}")
            threading.Thread(target=self.handle_server_message, args=(s, new_server_id)).start()
            
            # Start a new election if this new server has a higher ID
            if new_server_id > self.id:
                self.start_election()
        except Exception as e:
            print(f"Failed to connect to server {new_server_id}: {e}")

    def send_to_server(self, target_server_id, message):
        if target_server_id in self.servers:
            try:
                self.servers[target_server_id][2].send(message.encode())
            except Exception as e:
                print(f"Failed to send message to server {target_server_id}: {e}")
                del self.servers[target_server_id]

    def handle_client_connection(self, client_socket, addr):
        if not self.is_leader:
            # Redirect client to the leader
            redirect_msg = json.dumps({
                "type": "REDIRECT",
                "leader": self.leader
            })
            client_socket.send(redirect_msg.encode())
            client_socket.close()
        else:
            # Handle client connection as leader
            self.clients[addr] = client_socket
            threading.Thread(target=self.client_handler, args=(client_socket, addr)).start()

    def client_handler(self, client_socket, addr):
        while not self.shutdown_event.is_set():
            try:
                message = client_socket.recv(BUFFER_SIZE)
                if not message:
                    break

                message_data = json.loads(message.decode())
                self.handle_client_message(client_socket, message_data)

            except Exception as e:
                print(f"Error handling client {addr}: {e}")
                break

        client_socket.close()
        print(f"Connection with client {addr} closed")
        if addr in self.clients:
            del self.clients[addr]

    def handle_client_message(self, client_socket, message):
        if self.is_leader:
            # Process the client message
            self.process_client_request(client_socket, message)
        else:
            # Forward the message to the leader
            leader_socket = self.servers.get(self.leader)
            if leader_socket:
                forward_msg = json.dumps({
                    "type": "FORWARDED_CLIENT_MESSAGE",
                    "client_addr": client_socket.getpeername(),
                    "message": message
                })
                leader_socket[2].send(forward_msg.encode())
            else:
                # Leader not found, inform client
                client_socket.send(json.dumps({"type": "ERROR", "message": "Leader unavailable"}).encode())

    def process_client_request(self, client_socket, message):
        # Implement client request processing here
        response = json.dumps({"type": "RESPONSE", "message": "Request processed"})
        client_socket.send(response.encode())

    def send_heartbeat(self):
        while self.running:
            if self.is_leader:
                heartbeat_msg = json.dumps({"type": "HEARTBEAT", "leader": self.id})
                for server_id, server_info in self.servers.items():
                    try:
                        server_info[2].send(heartbeat_msg.encode())
                    except Exception as e:
                        print(f"Failed to send heartbeat to server {server_id}: {e}")
            time.sleep(HEARTBEAT_INTERVAL)

    def start_election(self):
        print("Starting election")
        higher_servers = {id: server for id, server in self.servers.items() if id > self.id}
        
        print(f"Higher servers: {list(higher_servers.keys())}")
        
        if not higher_servers:
            self.become_leader()
            return

        election_msg = json.dumps({"type": "ELECTION", "id": self.id})
        for server_id in higher_servers:
            print(f"Sending election message to {server_id}")
            self.send_to_server(server_id, election_msg)
        
        # Wait for responses
        print(f"Waiting for {ELECTION_TIMEOUT} seconds for election responses")
        time.sleep(ELECTION_TIMEOUT)
        
        if not self.leader:
            self.become_leader()

    def become_leader(self):
        self.leader = self.id
        self.is_leader = True
        print(f"Becoming leader: {self.id}")
        self.announce_leader()

    def announce_leader(self):
        coordinator_msg = json.dumps({"type": "COORDINATOR", "leader": self.id})
        for server_id in list(self.servers.keys()):
            self.send_to_server(server_id, coordinator_msg)
        
        for client in list(self.clients.values()):
            try:
                client.send(coordinator_msg.encode())
            except Exception as e:
                print(f"Failed to send coordinator message to client: {e}")

    def handle_election_message(self, message, from_server_id):
        if message['id'] < self.id:
            response = json.dumps({"type": "ELECTION_RESPONSE", "id": self.id})
            self.send_to_server(from_server_id, response)
            self.start_election()
        else:
            print(f"Received election message from higher server {message['id']}")

    def handle_coordinator_message(self, message):
        self.leader = message['leader']
        self.is_leader = (self.leader == self.id)
        print(f"New leader is: {self.leader}")

    def handle_server_message(self, server_socket, from_server_id):
        while self.running:
            try:
                message = server_socket.recv(BUFFER_SIZE)
                if not message:
                    break

                message_data = json.loads(message.decode())
                if message_data['type'] == 'ELECTION':
                    self.handle_election_message(message_data, from_server_id)
                elif message_data['type'] == 'COORDINATOR':
                    self.handle_coordinator_message(message_data)
                elif message_data['type'] == 'HEARTBEAT':
                    self.last_heartbeat = time.time()
                elif message_data['type'] == 'FORWARDED_CLIENT_MESSAGE':
                    if self.is_leader:
                        self.process_client_request(server_socket, message_data['message'])
                    else:
                        # If we're not the leader, forward again (shouldn't happen in normal operation)
                        self.handle_client_message(server_socket, message_data['message'])

            except Exception as e:
                print(f"Error handling server message from {from_server_id}: {e}")
                break

        print(f"Connection with server {from_server_id} closed")
        if from_server_id in self.servers:
            del self.servers[from_server_id]

    def check_leader_status(self):
        while self.running:
            if not self.is_leader and time.time() - self.last_heartbeat > self.heartbeat_timeout:
                print("Leader seems to be down. Starting new election.")
                self.start_election()
            time.sleep(5)  # Check every 5 seconds

    def handle_connections(self, tcp_socket):
        while self.running:
            try:
                client_socket, addr = tcp_socket.accept()
                print(f"New connection from {addr}")
                
                identity = json.loads(client_socket.recv(BUFFER_SIZE).decode())
                
                if identity['type'] == 'SERVER':
                    new_server_id = identity['id']
                    self.servers[new_server_id] = (addr[0], addr[1], client_socket)
                    threading.Thread(target=self.handle_server_message, args=(client_socket, new_server_id)).start()
                elif identity['type'] == 'CLIENT':
                    self.handle_client_connection(client_socket, addr)

            except Exception as e:
                print(f"Error in connection handling: {e}")

    def run(self):
        udp_listener_thread = threading.Thread(target=self.udp_listener)
        udp_listener_thread.start()

        broadcast_thread = threading.Thread(target=self.broadcast_server_info)
        broadcast_thread.start()

        heartbeat_thread = threading.Thread(target=self.send_heartbeat)
        heartbeat_thread.start()

        leader_status_thread = threading.Thread(target=self.check_leader_status)
        leader_status_thread.start()

        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        tcp_socket.bind(('', TCP_PORT))
        tcp_socket.listen()
        print(f"TCP server listening on port {TCP_PORT}")

        connection_thread = threading.Thread(target=self.handle_connections, args=(tcp_socket,))
        connection_thread.start()

        while self.running:
            print("\nAvailable commands:")
            print("1. exit - Shut down the server")
            print("2. list_clients - Show connected clients")
            print("3. list_servers - Show known servers")
            print("4. leader - Show current leader")
            print("5. status - Show server status")
            cmd = input("Enter a command: ")
            
            if cmd == 'exit':
                self.running = False
                self.shutdown_event.set()
                tcp_socket.close()
                break
            elif cmd == 'list_clients':
                if self.clients:
                    print("Connected clients:")
                    for client in self.clients.keys():
                        print(f"  - {client}")
                else:
                    print("No clients connected.")
            elif cmd == 'list_servers':
                if self.servers:
                    print("Known servers:")
                    for server in self.servers.keys():
                        print(f"  - {server}")
                else:
                    print("No other servers known.")
            elif cmd == 'leader':
                if self.leader:
                    print(f"Current leader: {self.leader}")
                    if self.is_leader:
                        print("This server is the leader.")
                    else:
                        print("This server is not the leader.")
                else:
                    print("No leader elected yet.")
            elif cmd == 'status':
                print(f"Server ID: {self.id}")
                print(f"Is leader: {self.is_leader}")
                print(f"Current leader: {self.leader}")
                print(f"Number of connected clients: {len(self.clients)}")
                print(f"Number of known servers: {len(self.servers)}")
            else:
                print("Invalid command. Please try again.")

        udp_listener_thread.join()
        broadcast_thread.join()
        heartbeat_thread.join()
        leader_status_thread.join()
        connection_thread.join()

if __name__ == "__main__":
    server = Server()
    server.run()