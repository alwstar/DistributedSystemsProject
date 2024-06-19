import socket
import struct
import threading
import json

MULTICAST_GROUP = '224.1.1.1'
MULTICAST_PORT = 5004
SERVER_PORT = 5005
BUFFER_SIZE = 1024

class Server:
    def __init__(self):
        self.local_ip = socket.gethostbyname(socket.gethostname())
        self.group_view = []
        self.leader = None

    def listen_multicast(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', MULTICAST_PORT))
        group = socket.inet_aton(MULTICAST_GROUP)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        while True:
            data, _ = sock.recvfrom(BUFFER_SIZE)
            message = json.loads(data.decode('utf-8'))
            self.process_message(message)

    def process_message(self, message):
        if message['ip'] not in self.group_view:
            self.group_view.append(message['ip'])
            self.elect_leader()
        print(f"[Server - Group View: {self.group_view}]")

    def elect_leader(self):
        if self.leader is None or self.leader not in self.group_view:
            self.leader = min(self.group_view)
            print(f"New Leader elected: {self.leader}")

    def forward_message(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('', SERVER_PORT))
        while True:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            message = json.loads(data.decode('utf-8'))
            self.forward_to_group(message)

    def forward_to_group(self, message):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for ip in self.group_view:
            sock.sendto(json.dumps(message).encode('utf-8'), (ip, MULTICAST_PORT))

    def start(self):
        threading.Thread(target=self.listen_multicast).start()
        threading.Thread(target=self.forward_message).start()

if __name__ == "__main__":
    server = Server()
    server.start()
