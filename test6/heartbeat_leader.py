import socket
import time
import pickle

SERVER_LIST = []
LEADER = ''
SERVER_IP = '127.0.0.1'
HEARTBEAT_PORT = 10000
ELECTION_PORT = 10001
LEADER_NOTIFICATION_PORT = 10002

def start_heartbeat():
    while True:
        for ip in SERVER_LIST:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(2)
                s.connect((ip, HEARTBEAT_PORT))
                s.send("Heartbeat".encode())
                response = s.recv(1024)
                print(f'Heartbeat response from {ip}: {response.decode()}')
            except socket.error:
                print(f'No heartbeat response from {ip}')
                if LEADER == ip:
                    print('Leader crash detected, starting election...')
                    start_leader_election(SERVER_LIST, SERVER_IP)
            finally:
                s.close()
        time.sleep(3)

def start_leader_election(server_list, ip):
    current_participants = [ip] + server_list
    ring = sorted(current_participants)
    neighbour = ring[(ring.index(ip) + 1) % len(ring)]
    send_election_message(neighbour, ip)

def send_election_message(neighbour, msg):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((neighbour, ELECTION_PORT))
        sock.send(msg.encode())
    except socket.error:
        pass
    finally:
        sock.close()

def receive_election_message():
    server_address = ('', ELECTION_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(server_address)
    sock.listen()
    while True:
        conn, address = sock.accept()
        response = conn.recv(1024).decode()
        if response == SERVER_IP:
            global LEADER
            LEADER = SERVER_IP
            send_new_leader_message()
        elif response > SERVER_IP:
            send_election_message(response)
        else:
            pass

def send_new_leader_message():
    msg = SERVER_IP
    for ip in SERVER_LIST:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        try:
            s.connect((ip, LEADER_NOTIFICATION_PORT))
            s.send(msg.encode())
        finally:
            s.close()

def receive_new_leader_message():
    server_address = ('', LEADER_NOTIFICATION_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(server_address)
    sock.listen()
    while True:
        conn, address = sock.accept()
        new_leader_ip = conn.recv(1024).decode()
        global LEADER
        LEADER = new_leader_ip
        conn.send('ack'.encode())
