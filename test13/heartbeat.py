import socket
import time
import logging
import multicast_data
import server_data
import ports
import thread_helper
import leader_election

def start_heartbeat():
    msg = "Heartbeat"
    while server_data.HEARTBEAT_RUNNING:
        time.sleep(3)
        multicast_data.SERVER_LIST = list(set(multicast_data.SERVER_LIST))
        for ip in multicast_data.SERVER_LIST:
            time.sleep(1)
            if server_data.isReplicaUpdated:
                server_data.HEARTBEAT_RUNNING = False
                break
            try:
                with socket.create_connection((ip, ports.HEARTBEAT_PORT), timeout=2) as s:
                    s.send(msg.encode())
                    response = s.recv(1024).decode()
                    logging.info(f'Received Heartbeat response: {response}')
            except (socket.timeout, socket.error):
                logging.warning(f'No response from: {ip}')
                handle_server_failure(ip)
        if not server_data.HEARTBEAT_RUNNING:
            print('Heartbeat stopped')
            break
    restart_heartbeat()

def handle_server_failure(ip):
    if ip in multicast_data.SERVER_LIST:
        multicast_data.SERVER_LIST.remove(ip)
        if multicast_data.LEADER == ip:
            logging.info('Leader crash detected')
            server_data.LEADER_CRASH = True
            server_data.LEADER_AVAILABLE = False
        server.update_server_list(multicast_data.SERVER_LIST)

def listen_heartbeat():
    server_address = ('', ports.HEARTBEAT_PORT)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(server_address)
        s.listen()
        print(f'Listening to Heartbeat on Port: {ports.HEARTBEAT_PORT}')
        while True:
            connection, _ = s.accept()
            with connection:
                heartbeat_msg = connection.recv(1024).decode()
                logging.info(f'Received Heartbeat from: {connection.getpeername()}')
                connection.sendall(heartbeat_msg.encode())

def restart_heartbeat():
    if server_data.isReplicaUpdated:
        server_data.isReplicaUpdated = False
        if server_data.LEADER_CRASH:
            server_data.LEADER_CRASH = False
            leader_election.start_leader_election(multicast_data.SERVER_LIST, server_data.SERVER_IP)
        server_data.HEARTBEAT_RUNNING = True
        thread_helper.newThread(start_heartbeat, ())

if __name__ == '__main__':
    start_heartbeat()
    listen_heartbeat()
