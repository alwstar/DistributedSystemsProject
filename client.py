# client.py

import socket
import threading
import os
from time import sleep
import hosts
import ports
import send_broadcast

def new_thread(target, args):
    t = threading.Thread(target=target, args=args)
    t.daemon = True
    t.start()

def send_message():
    global sock
    while True:
        message = input("")
        try:
            sock.send(message.encode(hosts.unicode))
        except Exception as e:
            print(e)
            break

def receive_message():
    global sock
    while True:
        try:
            data = sock.recv(hosts.buffer_size)
            if not data:
                raise Exception("Server disconnected")
            print(data.decode(hosts.unicode))
        except Exception as e:
            print(e)
            sock.close()
            sleep(3)
            connect()

def connect():
    global sock
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_exist = send_broadcast.sending_join_chat_request_to_broadcast()

    if server_exist:
        leader_address = (hosts.leader, ports.server)
        print(f'This is the server leader: {leader_address}')
        try:
            sock.connect(leader_address)
            sock.send('JOIN'.encode(hosts.unicode))
            print("You joined the Chat Room.\nYou can start chatting.")
        except Exception as e:
            print(f"Failed to connect to server leader: {e}")
            os._exit(0)
    else:
        print("Please try to join later again.")
        os._exit(0)

if __name__ == '__main__':
    try:
        print("You try to join the chat room.")
        connect()
        new_thread(send_message, ())
        new_thread(receive_message, ())
        while True:
            pass
    except KeyboardInterrupt:
        print("\nYou left the chatroom")
