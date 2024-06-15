import socket
import threading
import json
import time
import random
import string

# Server configuration
my_uid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
my_ip = '127.0.0.1'
ring_port = 10001
is_leader = False
leader_uid = None

# Participants in the ring
participants = [('127.0.0.1', 10001), ('127.0.0.1', 10002)]  # Update with actual participant addresses
clients = []

# Define replica class for replication
class Replica:
    def __init__(self, name):
        self.name = name
        self.data = None

    def store(self, data):
        print(f"{self.name} storing data: {data}")
        self.data = data

    def sync(self, data):
        print(f"{self.name} syncing data: {data}")
        self.data = data

    def read(self):
        return self.data

# Replicated database class
class ReplicatedDatabase:
    def __init__(self, replicas):
        self.replicas = replicas
        self.primary = replicas[0]

    def write(self, data):
        if is_leader:
            self.primary.store(data)
            for replica in self.replicas:
                replica.sync(data)

    def read(self):
        return self.primary.read()

# Initialize replicas and database
replicas = [Replica("Replica1"), Replica("Replica2"), Replica("Replica3")]
db = ReplicatedDatabase(replicas)

# Election-related functions
heartbeat_status = {}  # Define heartbeat_status dictionary

def get_next_participant():
    idx = participants.index((my_ip, ring_port))
    return participants[(idx + 1) % len(participants)]

def send_election_message(recipient, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(json.dumps(message).encode(), recipient)

def election_listener():
    global is_leader, leader_uid
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((my_ip, ring_port))
    print(f"Election listener started on {my_ip}:{ring_port}")

    while True:
        data, addr = sock.recvfrom(1024)
        message = json.loads(data.decode())
        print(f"Election message received: {message} from {addr}")
        if message['isLeader']:
            leader_uid = message['mid']
            is_leader = (message['mid'] == my_uid)
            print(f"Leader is now {message['mid']}")
        else:
            if message['mid'] > my_uid:
                send_election_message(get_next_participant(), message)
            elif message['mid'] < my_uid:
                message['mid'] = my_uid
                send_election_message(get_next_participant(), message)
            else:
                leader_uid = my_uid
                is_leader = True
                message['isLeader'] = True
                send_election_message(get_next_participant(), message)
                print(f"I am the leader: {my_uid}")

def start_leader_election():
    global is_leader, leader_uid
    print("Starting leader election...")
    election_message = {"mid": my_uid, "isLeader": False}
    send_election_message(get_next_participant(), election_message)

def handle_client(client_socket, addr):
    global db
    try:
        client_socket.send("Welcome! Please enter your name: ".encode())
        name = client_socket.recv(1024).decode().strip()
        print(f"{name} has joined from {addr}")
        
        while True:
            message = client_socket.recv(1024).decode().strip()
            if message:
                print(f"Received message: {message}")
                if is_leader:
                    db.write(message)
                else:
                    print("Not the leader, cannot write data.")
                client_socket.send(f"Data stored: {message}".encode())
            else:
                print(f"Connection from {addr} has been closed.")
                client_socket.close()
                break
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
        client_socket.close()

def start_server():
    election_thread = threading.Thread(target=election_listener)
    election_thread.start()

    heartbeat_listener_thread = threading.Thread(target=heartbeat_listener)
    heartbeat_listener_thread.start()

    heartbeat_thread = threading.Thread(target=send_heartbeat)
    heartbeat_thread.start()

    heartbeat_checker_thread = threading.Thread(target=check_heartbeats)
    heartbeat_checker_thread.start()

    broadcast_thread = threading.Thread(target=broadcast_listener)
    broadcast_thread.start()

    start_leader_election()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 9999))
    server_socket.listen(5)
    print(f"Server listening on port 9999")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr} has been established.")
        clients.append(client_socket)
        client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_thread.start()

def send_heartbeat():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        for participant in participants:
            if participant != (my_ip, ring_port):
                message = json.dumps({"type": "heartbeat"}).encode()
                sock.sendto(message, (participant[0], participant[1] + 1))
        time.sleep(2)
        print("Heartbeat sent")

def check_heartbeats():
    global is_leader, leader_uid
    while True:
        current_time = time.time()
        for participant in participants:
            if participant != (my_ip, ring_port):
                if (participant in heartbeat_status and
                        current_time - heartbeat_status[participant] > 5):
                    print(f"{participant} is down")
                    if leader_uid == participant[0]:
                        print("Leader is down, starting election...")
                        leader_uid = None
                        start_leader_election()
        time.sleep(2)

def heartbeat_listener():
    global heartbeat_status
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((my_ip, ring_port + 1))  # Using a different port for heartbeat messages
    print(f"Heartbeat listener started on {my_ip}:{ring_port + 1}")

    while True:
        data, addr = sock.recvfrom(1024)
        try:
            message = json.loads(data.decode())
            print(f"Heartbeat message received from {addr}")
            if 'type' in message and message['type'] == 'heartbeat':
                heartbeat_status[addr] = time.time()
        except (json.JSONDecodeError, KeyError):
            print(f"Received malformed heartbeat message from {addr}: {data}")

def broadcast_listener():
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    broadcast_socket.bind(('', 37020))
    print("Listening for broadcast messages on port 37020")

    while True:
        data, addr = broadcast_socket.recvfrom(1024)
        if data.decode() == "DISCOVER_SERVER":
            response_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            response_socket.sendto("SERVER_HERE".encode(), addr)
            print(f"Responded to discovery from {addr}")

if __name__ == "__main__":
    start_server()
