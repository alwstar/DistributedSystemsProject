import socket
import time
import multicast_data
import ports

def send_heartbeat():
    """
    Sends heartbeat messages to all servers in the server list periodically.
    """
    while True:
        for server in multicast_data.SERVER_LIST:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((server, ports.HEARTBEAT_PORT))
                    s.sendall(b'HEARTBEAT')
                    response = s.recv(1024)
                    print(f"Heartbeat acknowledged by {server}: {response}")
            except:
                print(f"Failed to send heartbeat to {server}")
                multicast_data.SERVER_LIST.remove(server)
                print(f"Removed {server} from server list due to failure.")
        time.sleep(2)

def listen_for_heartbeat():
    """
    Listens for heartbeat messages from other servers.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', ports.HEARTBEAT_PORT))
    sock.listen()

    while True:
        conn, addr = sock.accept()
        data = conn.recv(1024)
        if data:
            conn.sendall(data)  # Echo back the heartbeat message
            print(f"Received heartbeat from {addr}")
