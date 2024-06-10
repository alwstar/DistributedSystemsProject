import socket
import threading
import uuid
import json

my_uid = str(uuid.uuid1())
my_ip = '127.0.0.1'
ring_port = 10001
participants = [('127.0.0.1', 10002), ('127.0.0.1', 10003)]  # Beispielteilnehmer

def send_election_message(recipient, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(json.dumps(message).encode(), recipient)

def receive_messages():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((my_ip, ring_port))

    while True:
        data, addr = sock.recvfrom(1024)
        message = json.loads(data.decode())
        print(f"Received message: {message} from {addr}")
        
        if message['isLeader']:
            print(f"Leader elected: {message['mid']}")
        else:
            handle_election_message(message)

def handle_election_message(message):
    if message['mid'] < my_uid:
        new_message = {"mid": my_uid, "isLeader": False}
        send_election_message(get_next_participant(), new_message)
    elif message['mid'] > my_uid:
        send_election_message(get_next_participant(), message)
    elif message['mid'] == my_uid:
        new_message = {"mid": my_uid, "isLeader": True}
        send_election_message(get_next_participant(), new_message)

def get_next_participant():
    idx = participants.index((my_ip, ring_port))
    return participants[(idx + 1) % len(participants)]

if __name__ == "__main__":
    election_message = {"mid": my_uid, "isLeader": False}
    send_election_message(get_next_participant(), election_message)
    receive_thread = threading.Thread(target=receive_messages)
    receive_thread.start()
