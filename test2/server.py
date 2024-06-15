import socket
import struct
import common
import logging
from time import sleep

logging.basicConfig(filename='server.log', level=logging.INFO, format='%(asctime)s:%(name)s:%(message)s')

def request_to_multicast():
    sleep(1)
    message = common.serialize([common.SERVER_LIST, common.LEADER])
    multicast_address = (common.MCAST_GRP, common.MCAST_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1)
    ttl = struct.pack('b', common.MULTICAST_TTL)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    sock.sendto(message, multicast_address)
    print(f'\nMulticast sending data to receivers from {common.SERVER_IP} to {multicast_address}')

    try:
        sock.recvfrom(1024)
        if common.LEADER == common.SERVER_IP:
            print(f'{sock.getsockname()[0]}: Sending updates to all servers\n')
        return True
    except socket.timeout:
        print(f'{common.SERVER_IP}: Currently no receiver reachable')
        return False

def send_leader():
    if common.LEADER == common.SERVER_IP and len(common.SERVER_LIST) > 0:
        for i in range(len(common.SERVER_LIST)):
            replica = common.SERVER_LIST[i]
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            try:
                sock.connect((replica, common.LEADER_NOTIFICATION_PORT))
                leader_message = common.serialize(common.LEADER)
                sock.send(leader_message)
                logging.info(f'Leader {common.LEADER} is updating the leader parameter for {replica}')
                print(f'Updating Leader for {replica}')
            except:
                logging.critical(f'Failed to update leader address for {replica}')
                print(f'Failed to send Leader address to {replica}')
            finally:
                sock.close()

def receive_leader():
    server_address = ('', common.LEADER_NOTIFICATION_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(server_address)
    sock.listen()

    while True:
        connection, leader_address = sock.accept()
        leader = common.deserialize(connection.recv(1024))
        
        common.LEADER = leader
        print(f'LEADER IS: {common.LEADER}')

def send_server_list():
    if common.LEADER == common.SERVER_IP and len(common.SERVER_LIST) > 0:
        for i in range(len(common.SERVER_LIST)):
            if common.SERVER_LIST[i] != common.SERVER_IP:
                replica = common.SERVER_LIST[i]
                ip = replica
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sleep(1)
                try:
                    sock.connect((ip, common.SERVERLIST_UPDATE_PORT))
                    updated_list = common.serialize(common.SERVER_LIST)
                    sock.send(updated_list)
                    logging.info(f'Updating Server List for {ip}')
                    print(f'Updating Server List for {ip}')
                except:
                    logging.critical(f'failed to send serverlist {ip}')
                    print(f'failed to send serverlist {ip}')
                finally:
                    sock.close()

def receive_server_list():
    server_address = ('', common.SERVERLIST_UPDATE_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(server_address)
    sock.listen()

    while True:
        connection, leader_address = sock.accept()
        leader_list = common.deserialize(connection.recv(1024))
        common.SERVER_LIST = leader_list
        print(f'NEW SERVER LIST {common.SERVER_LIST}')
        sleep(0.5)
        update_server_list(common.SERVER_LIST)

def send_client_list():
    if common.LEADER == common.SERVER_IP and len(common.CLIENT_LIST) > 0:
        for i in range(len(common.CLIENT_LIST)):
            if common.CLIENT_LIST[i] != common.SERVER_IP:
                ip = common.CLIENT_LIST[i]
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                try:
                    sock.connect((ip, common.CLIENT_LIST_UPDATE_PORT))
                    updated_list = common.serialize(common.CLIENT_LIST)
                    sock.send(updated_list)
                    logging.info(f'Updating Client List for {ip}')
                    print(f'Updating Client List for {ip}')
                except:
                    logging.critical(f'failed to send Client List to {ip}')
                    print(f'failed to send Client list to {ip}')
                finally:
                    sock.close()

def receive_client_list():
    server_address = ('', common.CLIENT_LIST_UPDATE_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(server_address)
    sock.listen()

    while True:
        connection, leader_address = sock.accept()
        leader_list = common.deserialize(connection.recv(1024))
        common.CLIENT_LIST = leader_list
        print(f'NEW CLIENT LIST {common.CLIENT_LIST}')

def update_server_list(new_list):
    if len(common.SERVER_LIST) == 0:
        common.HEARTBEAT_RUNNING = False
        common.HEARTBEAT_COUNT = 0
        if common.LEADER != common.SERVER_IP:
            common.LEADER = common.SERVER_IP
            print(f'My server list is empty, the new leader is me {common.SERVER_IP}')
    elif len(common.SERVER_LIST) > 0:
        if common.HEARTBEAT_COUNT == 0:
            common.HEARTBEAT_COUNT += 1
            sleep(1)
            print(f'NEW LIST {list(set(new_list))}')
            common.SERVER_LIST = list(set(new_list))
            print(f'Heartbeat starting for the first time with the server list containing: {common.SERVER_LIST}')
            common.HEARTBEAT_RUNNING = True
            common.new_thread(start_heartbeat)
        else:
            common.SERVER_LIST = list(set(new_list))
            common.isReplicaUpdated = True

def new_client_message(client, address):
    while True:
        try:
            data = client.recv(1024)
            if data.decode('utf-8') != "":
                print(f'{common.SERVER_IP}: new Message from {address[0]}: {data.decode("utf-8")}')
                common.CLIENT_MESSAGES.append(f'{common.SERVER_IP}: new Message from {address[0]}: {data.decode("utf-8")}')
                send_new_client_message(address[0], data.decode('utf-8'))
        except Exception as err:
            print(err)
            break

def bind_server_sock():
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        host_address = (common.SERVER_IP, common.SERVER_PORT_FOR_CLIENTS)
        print(f'Server started on IP {common.SERVER_IP} and PORT {common.SERVER_PORT_FOR_CLIENTS}')
        server_socket.bind(host_address)
        server_socket.listen()
        print(f'Server is waiting for client connections...')
        while True:
            try:
                client, address = server_socket.accept()
                print(f"Accepted connection from {address}")
                client_data = client.recv(1024)
                if client_data:
                    print(f'{common.SERVER_IP}: Client {address[0]} is now connected')
                    common.new_thread(new_client_message, (client, address))
            except Exception as err:
                print(err)
                break
    except socket.error as err:
        print(f'Could not start Server. Error: {err}')
        sys.exit()

def start_heartbeat():
    failed_server = -1
    msg = "Heartbeat"
    while common.HEARTBEAT_RUNNING:
        sleep(3)
        common.SERVER_LIST = list(set(common.SERVER_LIST))
        for x in range(len(common.SERVER_LIST)):
            sleep(1)
            if x > len(common.SERVER_LIST):
                update_server_list(common.SERVER_LIST)
                send_server_list()
                break
            if common.isReplicaUpdated:
                common.HEARTBEAT_RUNNING = False
                break
            sleep(1)
            try:
                ip = common.SERVER_LIST[x]
            except IndexError:
                common.SERVER_LIST = list(set(common.SERVER_LIST))
                send_server_list()
                break
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            try:
                s.connect((ip, common.HEARTBEAT_PORT))
                s.send(msg.encode())
                try:
                    response = s.recv(1024)
                except socket.timeout:
                    pass
            except:
                failed_server = x
                if common.LEADER == ip:
                    common.LEADER_CRASH = True
                    common.LEADER_AVAILABLE = False
                else:
                    pass
                del common.SERVER_LIST[failed_server]
            finally:
                s.close()
        if failed_server >= 0:
            new_server_list = common.SERVER_LIST
            if common.LEADER_CRASH:
                print(f'Leader Server {ip} crashed and removed from the Server list')
            else:
                print(f'Removed crashed server: {ip}')
            update_server_list(new_server_list)
            common.HEARTBEAT_RUNNING = False
            break
        if not common.HEARTBEAT_RUNNING:
            print('Heartbeat stopped')
            break
    restart_heartbeat()

def listen_heartbeat():
    server_address = ('', common.HEARTBEAT_PORT)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(server_address)
    s.listen()
    print(f'Listening to Heartbeat on Port: {common.HEARTBEAT_PORT}')
    while True:
        connection, server_address = s.accept()
        heartbeat_msg = connection.recv(1024).decode()
        if heartbeat_msg:
            connection.sendall(heartbeat_msg.encode())

def restart_heartbeat():
    if common.isReplicaUpdated:
        common.isReplicaUpdated = False
        if common.LEADER_CRASH:
            common.LEADER_CRASH = False
            print('Starting Leader Election')
            start_leader_election(common.SERVER_LIST, common.SERVER_IP)
        common.HEARTBEAT_RUNNING = True
        common.new_thread(start_heartbeat)

def start_receiver():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', common.MCAST_PORT))
    group = socket.inet_aton(common.MCAST_GRP)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    print(f'\n{common.SERVER_IP}: Started UDP Socket to listen on Port {common.MCAST_PORT}')
    while True:
        try:
            data, address = sock.recvfrom(1024)
            print(f"Received data from {address}: {data}")
            if address[0] != common.SERVER_IP:
                print(f'{common.SERVER_IP}: Received data from {address} \n')
            if common.LEADER == common.SERVER_IP and common.deserialize(data)[0] == 'JOIN':
                common.CLIENT_LIST.append(address[0]) if address[0] not in common.CLIENT_LIST else common.CLIENT_LIST
                message = common.serialize([common.LEADER, ''])
                sock.sendto(message, address)
                send_client_list()
                print(f'{common.SERVER_IP}: "{address}" wants to join the Chat Room\n')
            if len(common.deserialize(data)[0]) == 0:
                common.SERVER_LIST.append(address[0]) if address[0] not in common.SERVER_LIST else common.SERVER_LIST
                print(f'{common.SERVER_IP}: replica server joined {address}')
                common.replica_data.append(address)
                update_server_list(common.SERVER_LIST)
                send_server_list()
                send_leader()
                print(common.replica_data)
                sock.sendto('ack'.encode('utf-8'), address)
                common.network_state = True
            elif common.deserialize(data)[0] != 'JOIN' and common.LEADER != common.SERVER_IP:
                sock.sendto('ack'.encode('utf-8'), address)
                common.network_changed = True
        except KeyboardInterrupt:
            sock.close()
            print(f'{common.SERVER_IP}: Closing Socket')

def start_leader_election(server_list, ip):
    current_participants = [ip]
    current_participants.extend(server_list)
    if len(server_list) == 1:
        global neighbour
        neighbour = server_list[0]
        send_election_message(ip)
    else:
        ring = form_ring(current_participants)
        neighbour = get_neighbour(ring, ip, 'right')
        send_election_message(ip)

def send_election_message(msg):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        sock.connect((neighbour, common.SERVER_ELECTION_PORT))
    except:
        pass
    try:
        sleep(1)
        sock.send(msg.encode())
    finally:
        sock.close()

def receive_election_message():
    server_address = ('', common.SERVER_ELECTION_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(server_address)
    sock.listen()
    while True:
        conn, address = sock.accept()
        response = conn.recv(1024).decode()
        sleep(2)
        if response == common.SERVER_IP:
            common.LEADER = common.SERVER_IP
            sendnew_leader_message()
        elif response > common.SERVER_IP:
            send_election_message(response)

def listenfor_new_leader_message():
    server_address = ('', common.NEW_LEADER_PORT)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(server_address)
    s.listen()
    while True:
        connection, server_address = s.accept()
        newleader_ip = connection.recv(1024).decode()
        response = 'ack msg.Received new leader information'
        connection.send(response.encode())
        common.LEADER = newleader_ip

def form_ring(members):
    sorted_binary_ring = sorted([socket.inet_aton(member) for member in members])
    sorted_ip_ring = [socket.inet_ntoa(node) for node in sorted_binary_ring]
    return sorted_ip_ring

def get_neighbour(ring, current_node_ip, direction='left'):
    current_node_index = ring.index(current_node_ip) if current_node_ip in ring else -1
    if current_node_index != -1:
        if direction == 'left':
            if current_node_index + 1 == len(ring):
                return ring[0]
            else:
                return ring[current_node_index + 1]
        else:
            if current_node_index == 0:
                return ring[len(ring) - 1]
            else:
                return ring[current_node_index - 1]
    else:
        return None

def sendnew_leader_message():
    if common.LEADER == common.SERVER_IP:
        msg = common.SERVER_IP
        for x in range(len(common.SERVER_LIST)):
            ip = common.SERVER_LIST[x]
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            try:
                s.connect((ip, common.NEW_LEADER_PORT))
                s.send(msg.encode())
                try:
                    response = s.recv(1024)
                except socket.timeout:
                    pass
            finally:
                s.close()

if __name__ == '__main__':
    if not request_to_multicast():
        common.LEADER = common.SERVER_IP
        common.LEADER_CRASH = False
        common.LEADER_AVAILABLE = True

    common.new_thread(start_receiver)
    common.new_thread(bind_server_sock)
    common.new_thread(receive_server_list)
    common.new_thread(receive_leader)
    common.new_thread(listen_heartbeat)
    common.new_thread(listenfor_new_leader_message)
    common.new_thread(receive_election_message)
    common.new_thread(receive_client_list)

    while True:
        try:
            if common.LEADER and common.network_state:
                request_to_multicast()
                common.network_state = False
            elif common.LEADER != common.SERVER_IP and common.network_state:
                common.network_state = False
        except KeyboardInterrupt:
            print(f'\nClosing Server for IP {common.SERVER_IP} on PORT {common.SERVER_PORT_FOR_CLIENTS}')
            break
