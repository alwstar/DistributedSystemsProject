import socket
import threading
import random
import string
import json
import time

clients = []
client_names = {}
server_name = "Server"
my_uid = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
my_ip = '127.0.0.1'
ring_port = 10001
is_leader = False
leader_uid = None

participants = [('127.0.0.1', 10001), ('127.0.0.1', 10002)]  # Update with actual participant addresses

heartbeat_interval = 2  # seconds
heartbeat_timeout = 5  # seconds
heartbeat_status = {}

def discover_other_servers():
    global server_name
    broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_socket.settimeout(2)
    
    server_count = 1
    try:
        for i in range(5):
            broadcast_socket.sendto("DISCOVER_SERVER".encode(), ('<broadcast>', 37020))
            while True:
                try:
                    data, addr = broadcast_socket.recvfrom(1024)
                    if data.decode() == "SERVER_HERE":
                        server_count += 1
                except socket.timeout:
                    break
    except Exception as e:
        print(f"Error discovering other servers: {e}")

    server_name = f"Server{server_count}"
    print(f"{server_name} is running.")

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

def broadcast(message, sender_socket):
    for client in clients:
        if client != sender_socket:
            try:
                client.send(message)
            except:
                client.close()
                clients.remove(client)

def handle_client(client_socket, addr):
    try:
        client_socket.send("Welcome! Please enter your name: ".encode())
        name = client_socket.recv(1024).decode().strip()
        client_names[client_socket] = name
        welcome_message = f"{name} has joined the chat!"
        broadcast(welcome_message.encode(), client_socket)
        print(welcome_message)

        while True:
            message = client_socket.recv(1024)
            if message:
                broadcast_message = f"{name}: {message.decode()}"
                print(broadcast_message)
                broadcast(broadcast_message.encode(), client_socket)
            else:
                client_socket.close()
                clients.remove(client_socket)
                broadcast(f"{name} has left the chat.".encode(), None)
                break
    except:
        client_socket.close()
        clients.remove(client_socket)
        if client_socket in client_names:
            name = client_names.pop(client_socket)
            broadcast(f"{name} has left the chat.".encode(), None)

def log_status():
    while True:
        print(f"{server_name} is {'active (Leader)' if is_leader else 'active'}")
        print("Current clients:")
        for name in client_names.values():
            print(f" - {name}")
        time.sleep(10)

def election_listener():
    global is_leader, leader_uid
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((my_ip, ring_port))

    while True:
        data, addr = sock.recvfrom(1024)
        message = json.loads(data.decode())
        if message['isLeader']:
            leader_uid = message['mid']
            is_leader = (message['mid'] == my_uid)
            print(f"Leader is now {message['mid']}")

def send_election_message(recipient, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(json.dumps(message).encode(), recipient)

def start_leader_election():
    global is_leader, leader_uid
    print("Starting leader election...")
    election_message = {"mid": my_uid, "isLeader": False}
    send_election_message(get_next_participant(), election_message)

def get_next_participant():
    idx = participants.index((my_ip, ring_port))
    return participants[(idx + 1) % len(participants)]

def heartbeat_listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((my_ip, ring_port + 1))  # Using a different port for heartbeat messages
    while True:
        data, addr = sock.recvfrom(1024)
        message = json.loads(data.decode())
        if message['type'] == 'heartbeat':
            heartbeat_status[addr] = time.time()

def send_heartbeat():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        for participant in participants:
            if participant != (my_ip, ring_port):
                message = json.dumps({"type": "heartbeat"}).encode()
                sock.sendto(message, (participant[0], participant[1] + 1))
        time.sleep(heartbeat_interval)

def check_heartbeats():
    global is_leader, leader_uid
    while True:
        current_time = time.time()
        for participant in participants:
            if participant != (my_ip, ring_port):
                if (participant in heartbeat_status and
                        current_time - heartbeat_status[participant] > heartbeat_timeout):
                    print(f"{participant} is down")
                    if leader_uid == participant[0]:
                        print("Leader is down, starting election...")
                        leader_uid = None
                        start_leader_election()
        time.sleep(heartbeat_interval)

def start_server():
    global server_name

    discover_other_servers()

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 9999))
    server_socket.listen(5)
    print(f"{server_name} listening on port 9999")

    broadcast_thread = threading.Thread(target=broadcast_listener)
    broadcast_thread.start()

    log_thread = threading.Thread(target=log_status)
    log_thread.start()

    election_thread = threading.Thread(target=election_listener)
    election_thread.start()

    heartbeat_listener_thread = threading.Thread(target=heartbeat_listener)
    heartbeat_listener_thread.start()

    heartbeat_sender_thread = threading.Thread(target=send_heartbeat)
    heartbeat_sender_thread.start()

    heartbeat_checker_thread = threading.Thread(target=check_heartbeats)
    heartbeat_checker_thread.start()

    start_leader_election()

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr} has been established.")
        client_socket.send(f"Connected to {server_name}".encode())
        clients.append(client_socket)
        client_thread = threading.Thread(target=handle_client, args=(client_socket, addr))
        client_thread.start()

if __name__ == "__main__":
    start_server()
