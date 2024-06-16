# server.py

import socket
import sys
import threading
import queue
import hosts
import ports
import receive_broadcast
import send_broadcast
import heartbeat

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
host_address = (hosts.myIP, ports.server)

FIFO = queue.Queue()

def printer():
    print(f'\n[SERVER] Server List: {hosts.server_list} ==> Leader: {hosts.leader}'
          f'\n[SERVER] Client List: {hosts.client_list}'
          f'\n[SERVER] Neighbour ==> {hosts.neighbour}\n')

def new_thread(target, args):
    t = threading.Thread(target=target, args=args)
    t.daemon = True
    t.start()

def send_clients():
    message = ''
    while not FIFO.empty():
        message += f'{FIFO.get()}'
        message += '\n' if not FIFO.empty() else ''
    if message:
        for member in hosts.client_list:
            member.send(message.encode(hosts.unicode))

def client_handler(client, address):
    while True:
        try:
            data = client.recv(hosts.buffer_size)
            if not data:
                print(f'{address} disconnected')
                FIFO.put(f'\n{address} disconnected\n')
                hosts.client_list.remove(client)
                client.close()
                break
            FIFO.put(f'{address} said: {data.decode(hosts.unicode)}')
            print(f'Message from {address} ==> {data.decode(hosts.unicode)}')
        except Exception as e:
            print(e)
            break

def start_binding():
    sock.bind(host_address)
    sock.listen()
    print(f'\n[SERVER] Starting and listening on IP {hosts.myIP} with PORT {ports.server}', file=sys.stderr)
    while True:
        try:
            client, address = sock.accept()
            data = client.recv(hosts.buffer_size)
            if data:
                print(f'{address} connected')
                FIFO.put(f'\n{address} connected\n')
                hosts.client_list.append(client)
                new_thread(client_handler, (client, address))
        except Exception as e:
            print(e)
            break

if __name__ == '__main__':
    broadcast_receiver_exist = send_broadcast.sending_request_to_broadcast()
    if not broadcast_receiver_exist:
        hosts.server_list.append(hosts.myIP)
        hosts.leader = hosts.myIP

    new_thread(receive_broadcast.starting_broadcast_receiver, ())
    new_thread(start_binding, ())
    new_thread(heartbeat.start_heartbeat, ())

    while True:
        try:
            if hosts.leader == hosts.myIP and hosts.network_changed or hosts.replica_crashed:
                if hosts.leader_crashed:
                    hosts.client_list = []
                send_broadcast.sending_request_to_broadcast()
                hosts.leader_crashed = False
                hosts.network_changed = False
                hosts.replica_crashed = ''
                printer()

            if hosts.leader != hosts.myIP and hosts.network_changed:
                hosts.network_changed = False
                printer()

            send_clients()

        except KeyboardInterrupt:
            sock.close()
            print(f'\nClosing Server on IP {hosts.myIP} with PORT {ports.server}', file=sys.stderr)
            break
