import socket
import struct
import pickle
import multicast_data
import ports
from threading import Thread

def multicast_listener():
    """
    Listens for multicast messages from other servers and handles them appropriately.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', multicast_data.MCAST_PORT))

    # Join the multicast group
    mreq = struct.pack("4sl", socket.inet_aton(multicast_data.MCAST_GRP), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    while True:
        data, addr = sock.recvfrom(1024)
        message = pickle.loads(data)
        handle_message(message, addr)

def handle_message(message, addr):
    """
    Handles incoming messages based on their type.
    """
    if message == "ELECTION_START":
        # Initiate leader election process
        start_leader_election()
    else:
        # Update server list
        multicast_data.SERVER_LIST = message
        print(f"Updated server list: {multicast_data.SERVER_LIST}")

def start_leader_election():
    # Placeholder function to start leader election
    print("Starting leader election...")
