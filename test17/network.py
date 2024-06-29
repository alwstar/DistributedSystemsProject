import socket
import threading
import json
from message import parse_message, MessageType, create_message
from logger import setup_logger

logger = setup_logger("network")

class NetworkManager:
    def __init__(self, udp_port, buffer_size):
        self.udp_port = udp_port
        self.buffer_size = buffer_size
        self.tcp_socket = None
        self.shutdown_event = threading.Event()

    def discover_server(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            udp_socket.bind(('', self.udp_port))
            logger.info("Waiting for server discovery message...")
            while not self.shutdown_event.is_set():
                try:
                    message, server_addr = udp_socket.recvfrom(self.buffer_size)
                    server_ip = server_addr[0]
                    server_data = json.loads(message.decode())
                    
                    if 'tcp_port' in server_data:
                        server_tcp_port = server_data['tcp_port']
                    elif 'content' in server_data and isinstance(server_data['content'], dict):
                        server_tcp_port = server_data['content'].get('tcp_port')
                    else:
                        logger.error(f"Received invalid server discovery message: {server_data}")
                        continue

                    if server_tcp_port:
                        logger.info(f"Discovered server at {server_ip} on port {server_tcp_port}")
                        return server_ip, int(server_tcp_port)
                    else:
                        logger.error("Received server discovery message without TCP port information")
                except json.JSONDecodeError:
                    logger.error(f"Received invalid JSON in server discovery message: {message.decode()}")
                except Exception as e:
                    logger.error(f"Error in server discovery: {e}")

    # ... (rest of the NetworkManager class remains the same)