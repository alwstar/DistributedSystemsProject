"""
Date:       25.12.2021  
Group:      10

LaLann-Chang-Roberts algorithm - Server leader election
"""
# import Modules
import os
import struct
import sys
import threading
import socket
import pickle
import logging

import multicast_data
import ports
import server_data
from server import *

neighbour = ''

# Sorted Ip
def form_ring(members):
    sorted_binary_ring = sorted([socket.inet_aton(member) for member in members])
    sorted_ip_ring = [socket.inet_ntoa(node) for node in sorted_binary_ring]
    return sorted_ip_ring

# get neighbour of IP
def get_neighbour(ring, current_node_ip):
    current_node_index = ring.index(current_node_ip) if current_node_ip in ring else -1
    if current_node_index != -1:
        if current_node_index + 1 == len(ring):
            return ring[0]
        else:
            return ring[current_node_index + 1]
    else:
        return None

# Publish new leader ip address
def send_new_leader_message():
    if multicast_data.LEADER == server_data.SERVER_IP:
        msg = server_data.SERVER_IP
        for ip in multicast_data.SERVER_LIST:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            try:
                s.connect((ip, ports.NEW_LEADER_PORT))
                s.send(msg.encode())
                try:
                    response = s.recv(1024)
                except socket.timeout:
                    pass
            finally:
                s.close()

def listen_for_new_leader_message():
    server_address = ('', ports.NEW_LEADER_PORT)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(server_address)
    s.listen()
    while True:
        connection, _ = s.accept()
        newleader_ip = connection.recv(1024).decode()
        response = 'ack msg.Received new leader information'
        connection.send(response.encode())
        multicast_data.LEADER = newleader_ip

def start_leader_election(server_list, ip):
    global neighbour
    current_participants = [ip] + server_list
    ring = form_ring(current_participants)
    neighbour = get_neighbour(ring, ip)
    send_election_message(ip)

def send_election_message(uid, is_leader=False):
    message = {
        "mid": uid,
        "isLeader": is_leader
    }
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        sock.connect((neighbour, ports.SERVER_ELECTION_PORT))
        sock.send(pickle.dumps(message))
    except:
        print('Connecting to neighbour was not possible')
    finally:
        sock.close()

def receive_election_message():
    server_address = ('', ports.SERVER_ELECTION_PORT)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(server_address)
    sock.listen()
    participant = False
    while True:
        conn, _ = sock.accept()
        response = pickle.loads(conn.recv(1024))
        mid = response['mid']
        is_leader = response['isLeader']
        if is_leader:
            multicast_data.LEADER = mid
            send_new_leader_message()
            participant = False
        elif mid < server_data.SERVER_IP and not participant:
            send_election_message(server_data.SERVER_IP)
            participant = True
        elif mid > server_data.SERVER_IP:
            send_election_message(mid)
            participant = True
        elif mid == server_data.SERVER_IP:
            send_election_message(server_data.SERVER_IP, True)
            participant = False

if __name__ == '__main__':
    start_leader_election(multicast_data.SERVER_LIST, server_data.SERVER_IP)
    listen_for_new_leader_message()
    receive_election_message()
