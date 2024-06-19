import socket
import struct
import threading
import json
import time

MULTICAST_GROUP = '224.1.1.1'
MULTICAST_PORT = 5004
BUFFER_SIZE = 1024

class ReliableMulticast:
    def __init__(self):
        self.local_ip = socket.gethostbyname(socket.gethostname())
        self.lamport_clock = 0
        self.group_view = []
        self.hold_back_queue = []
        self.delivery_queue = []

    def increment_clock(self):
        self.lamport_clock += 1
        return self.lamport_clock

    def send_message(self, message):
        self.increment_clock()
        message = json.dumps({
            'ip': self.local_ip,
            'clock': self.lamport_clock,
            'message': message
        }).encode('utf-8')
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(message, (MULTICAST_GROUP, MULTICAST_PORT))
        sock.close()

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
        self.hold_back_queue.append(message)
        self.hold_back_queue.sort(key=lambda x: x['clock'])
        self.deliver_messages()

    def deliver_messages(self):
        while self.hold_back_queue and self.hold_back_queue[0]['clock'] == self.lamport_clock + 1:
            message = self.hold_back_queue.pop(0)
            self.lamport_clock += 1
            self.delivery_queue.append(message)
            print(f"[{self.local_ip} - Clock: {self.lamport_clock}] Delivered: {message['message']} from {message['ip']}")

    def start(self):
        threading.Thread(target=self.listen_multicast).start()

if __name__ == "__main__":
    reliable_multicast = ReliableMulticast()
    reliable_multicast.start()
    while True:
        msg = input("Enter message: ")
        reliable_multicast.send_message(msg)
