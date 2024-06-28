import socket
import threading
import pickle
import multicast_data
import ports
from server_data import SERVER_IP

def elect_leader():
    """
    Elects a new leader from the list of servers.
    """
    if not multicast_data.SERVER_LIST:
        multicast_data.LEADER = SERVER_IP
        return SERVER_IP

    # Simple election: choose the server with the lowest IP address
    leader = sorted(multicast_data.SERVER_LIST)[0]
    multicast_data.LEADER = leader
    notify_leader_change(leader)
    return leader

def notify_leader_change(leader):
    """
    Notify all servers about the leader change.
    """
    for server in multicast_data.SERVER_LIST:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((server, ports.LEADER_NOTIFICATION_PORT))
                sock.sendall(pickle.dumps(leader))
                print(f"Notification sent to {server} about new leader {leader}")
        except Exception as e:
            print(f"Failed to notify {server} about the leader change: {e}")

def listen_for_election():
    """
    Listens for an election message to start a new leader election.
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('', ports.SERVER_ELECTION_PORT))
    server_socket.listen()
    print("Listening for leader election requests...")
    
    while True:
        client_socket, addr = server_socket.accept()
        data = client_socket.recv(1024)
        if data:
            threading.Thread(target=elect_leader).start()

def main():
    """
    Main function to handle leader election.
    """
    threading.Thread(target=listen_for_election).start()

if __name__ == '__main__':
    main()
