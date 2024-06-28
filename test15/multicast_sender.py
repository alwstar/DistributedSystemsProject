import socket
import struct
import pickle
import multicast_data
import ports
from time import sleep

# Setup multicast address and socket
multicast_address = (multicast_data.MCAST_GRP, multicast_data.MCAST_PORT)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
ttl = struct.pack('b', multicast_data.MULTICAST_TTL)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

def send_multicast_message(message):
    """
    Sends a multicast message to the multicast group.
    """
    serialized_msg = pickle.dumps(message)
    sock.sendto(serialized_msg, multicast_address)

def notify_server_list_update():
    """
    Notify all multicast group members about the server list update.
    """
    send_multicast_message(multicast_data.SERVER_LIST)

def notify_leader_election():
    """
    Notify all multicast group members to initiate leader election.
    """
    send_multicast_message("ELECTION_START")
