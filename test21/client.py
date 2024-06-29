import socket
import threading
import json
import time
import sys

BUFFER_SIZE = 1024
UDP_PORT = 5000  # This should match the UDP_PORT in the server code

class Client:
    def __init__(self):
        self.server_address = None
        self.socket = None
        self.running = True

    def discover_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            udp_socket.settimeout(5)  # Set a timeout for receiving responses

            discovery_message = json.dumps({"type": "DISCOVER"}).encode()
            
            print("Discovering servers...")
            attempts = 0
            while attempts < 3:  # Try 3 times before giving up
                try:
                    udp_socket.sendto(discovery_message, ('192.168.178.255', UDP_PORT))
                    while True:
                        try:
                            data, server = udp_socket.recvfrom(BUFFER_SIZE)
                            response = json.loads(data.decode())
                            if response['type'] == 'SERVER_ANNOUNCE':
                                print(f"Discovered server: {response['id']}")
                                return (server[0], response['tcp_port'])
                        except socket.timeout:
                            break
                except Exception as e:
                    print(f"Error during discovery: {e}")
                attempts += 1
                time.sleep(2)  # Wait before next attempt
            
            print("No servers discovered.")
            return None

    def connect_to_server(self, server_address=None):
        if server_address is None:
            server_address = self.discover_server()
            if server_address is None:
                return False

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print(f"Attempting to connect to server at {server_address}")
            self.socket.connect(server_address)
            
            # Send initial connection message
            self.socket.send(json.dumps({"type": "CLIENT"}).encode())
            
            # Handle potential redirection
            response = json.loads(self.socket.recv(BUFFER_SIZE).decode())
            if response['type'] == 'REDIRECT':
                self.socket.close()
                leader_address = response['leader'].split(':')
                print(f"Redirected to leader at {leader_address}")
                return self.connect_to_server((leader_address[0], int(leader_address[1])))
            
            print(f"Connected to server at {server_address}")
            self.server_address = server_address
            return True
        except Exception as e:
            print(f"Failed to connect to server at {server_address}: {e}")
            return False

    def send_message(self, message):
        try:
            self.socket.send(json.dumps({"type": "CLIENT_MESSAGE", "content": message}).encode())
            response = json.loads(self.socket.recv(BUFFER_SIZE).decode())
            print(f"Server response: {response['message']}")
        except Exception as e:
            print(f"Error sending message: {e}")

    def receive_messages(self):
        while self.running:
            try:
                message = self.socket.recv(BUFFER_SIZE)
                if not message:
                    break
                
                message_data = json.loads(message.decode())
                
                if message_data['type'] == 'HEARTBEAT':
                    # Send heartbeat response
                    self.socket.send(json.dumps({"type": "HEARTBEAT_RESPONSE"}).encode())
                elif message_data['type'] == 'COORDINATOR':
                    print(f"New leader announced: {message_data['leader']}")
                else:
                    print(f"Received message: {message_data}")

            except Exception as e:
                print(f"Error receiving message: {e}")
                break

        print("Disconnected from server")
        self.reconnect()

    def reconnect(self):
        while self.running:
            print("Attempting to reconnect...")
            if self.connect_to_server():
                threading.Thread(target=self.receive_messages).start()
                break
            time.sleep(5)

    def run(self):
        if self.connect_to_server():
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.start()

            while self.running:
                message = input("Enter message (or 'exit' to quit): ")
                if message.lower() == 'exit':
                    self.running = False
                    self.socket.close()
                    break
                self.send_message(message)

            receive_thread.join()
        else:
            print("Failed to connect to any server. Exiting.")

if __name__ == "__main__":
    client = Client()
    client.run()