# Client Operations

import socket
import threading
import os
from time import sleep
from config import *

def connect():
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    leader_address = (LEADER, SERVER_PORT)
    try:
        sock.connect(leader_address)
        sock.send('JOIN'.encode(UNICODE))
    except:
        os._exit(0)

def send_message():
    global sock
    while True:
        message = input("")
        try:
            sock.send(message.encode(UNICODE))
        except:
            break

def receive_message():
    global sock
    while True:
        try:
            data = sock.recv(BUFFER_SIZE)
            print(data.decode(UNICODE))
            if not data:
                sock.close()
                sleep(3)
                connect()
        except:
            break

if __name__ == '__main__':
    connect()
    threading.Thread(target=send_message).start()
    threading.Thread(target=receive_message).start()
    while True:
        pass
