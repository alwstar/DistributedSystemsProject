import socket
import threading
import json
import time

BROADCAST_IP = '192.168.178.255'
BROADCAST_PORT = 5004
BUFFER_SIZE = 1024
HEARTBEAT_INTERVAL = 5
HEARTBEAT_TIMEOUT = 15

class Server:
    def __init__(self):
        self.local_ip = socket.gethostbyname(socket.gethostname())
        self.group_view = {}
        self.leader = None

    def broadcast_message(self, message_data):
        message = json.dumps(message_data).encode('utf-8')
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.sendto(message, (BROADCAST_IP, BROADCAST_PORT))
        sock.close()

    def send_heartbeat(self):
        while True:
            time.sleep(HEARTBEAT_INTERVAL)
            message_data = {
                'type': 'heartbeat',
                'ip': self.local_ip
            }
            self.broadcast_message(message_data)

    def listen_for_messages(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', BROADCAST_PORT))
        while True:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            message = json.loads(data.decode('utf-8'))
            self.process_message(message)

    def process_message(self, message):
        if message['type'] == 'discovery':
            response = {
                'type': 'discovery_response',
                'ip': self.local_ip
            }
            self.broadcast_message(response)
        elif message['type'] == 'heartbeat':
            self.group_view[message['ip']] = time.time()
            if message['ip'] not in self.group_view:
                print(f"Server {message['ip']} joined the network.")
        elif message['type'] == 'chat':
            print(f"Received chat from {message['ip']}: {message['message']}")

    def check_heartbeats(self):
        while True:
            time.sleep(HEARTBEAT_TIMEOUT)
            current_time = time.time()
            for server_ip, last_heartbeat in list(self.group_view.items()):
                if current_time - last_heartbeat > HEARTBEAT_TIMEOUT:
                    print(f"Server {server_ip} is considered down.")
                    del self.group_view[server_ip]

    def elect_leader(self):
        while True:
            if not self.leader or self.leader not in self.group_view:
                self.leader = min(self.group_view.keys(), default=self.local_ip)
                print(f"New leader elected: {self.leader}")
            time.sleep(HEARTBEAT_INTERVAL)

    def start(self):
        threading.Thread(target=self.listen_for_messages).start()
        threading.Thread(target=self.send_heartbeat).start()
        threading.Thread(target=self.check_heartbeats).start()
        threading.Thread(target=self.elect_leader).start()

if __name__ == "__main__":
    server = Server()
    server.start()
