import socket
import threading
import json
import time

BROADCAST_IP = '192.168.178.255'
BROADCAST_PORT = 5004
BUFFER_SIZE = 1024

class Client:
    def __init__(self):
        self.local_ip = socket.gethostbyname(socket.gethostname())
        self.group_view = []

    def send_message(self, message):
        message_data = {
            'type': 'chat',
            'ip': self.local_ip,
            'message': message
        }
        self.broadcast_message(message_data)

    def broadcast_message(self, message_data):
        message = json.dumps(message_data).encode('utf-8')
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(message, (BROADCAST_IP, BROADCAST_PORT))
        sock.close()

    def listen_for_messages(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', BROADCAST_PORT))
        while True:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            message = json.loads(data.decode('utf-8'))
            self.process_message(message)

    def process_message(self, message):
        if message['type'] == 'chat':
            print(f"Received message from {message['ip']}: {message['message']}")
        elif message['type'] == 'heartbeat':
            print(f"Heartbeat received from server {message['ip']}")
        elif message['type'] == 'discovery_response':
            if message['ip'] not in self.group_view:
                self.group_view.append(message['ip'])
                print(f"New server discovered: {message['ip']}")

    def discover_servers(self):
        message_data = {
            'type': 'discovery',
            'ip': self.local_ip
        }
        self.broadcast_message(message_data)

    def start(self):
        threading.Thread(target=self.listen_for_messages).start()
        self.discover_servers()
        while True:
            msg = input("Enter message: ")
            self.send_message(msg)

if __name__ == "__main__":
    client = Client()
    client.start()
