import socket
import threading
from network import NetworkManager
from election import ElectionManager
from message import MessageType, create_message, parse_message
from logger import setup_logger

logger = setup_logger("server")

class Server:
    def __init__(self, tcp_port, udp_port, buffer_size):
        self.tcp_port = tcp_port
        self.udp_port = udp_port
        self.buffer_size = buffer_size
        self.clients = {}
        self.election = ElectionManager(self.tcp_port, self.broadcast_message)
        self.shutdown_event = threading.Event()

    def start(self):
        threading.Thread(target=self.udp_broadcast, daemon=True).start()
        
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
            tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            tcp_socket.bind(('', self.tcp_port))
            tcp_socket.listen()
            logger.info(f"TCP server listening on port {self.tcp_port}")

            while not self.shutdown_event.is_set():
                try:
                    client_socket, addr = tcp_socket.accept()
                    self.clients[addr] = client_socket
                    logger.info(f"New connection from {addr}")
                    threading.Thread(target=self.handle_client, args=(client_socket, addr), daemon=True).start()
                except Exception as e:
                    logger.error(f"Error accepting connection: {e}")

    def udp_broadcast(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            while not self.shutdown_event.is_set():
                try:
                    message = create_message(MessageType.HEARTBEAT, {"tcp_port": self.tcp_port})
                    udp_socket.sendto(message.encode(), ('<broadcast>', self.udp_port))
                    self.shutdown_event.wait(10)
                except Exception as e:
                    logger.error(f"Error in UDP broadcast: {e}")

    def handle_client(self, client_socket, addr):
        while not self.shutdown_event.is_set():
            try:
                message = client_socket.recv(self.buffer_size)
                if not message:
                    break
                self.process_message(parse_message(message.decode()), addr)
            except Exception as e:
                logger.error(f"Error handling client {addr}: {e}")
                break
        self.remove_client(addr)

    def process_message(self, message, sender_addr):
        if message['type'] == MessageType.CHAT:
            self.forward_message(message)
        elif message['type'] in (MessageType.ELECTION, MessageType.LEADER):
            self.broadcast_message(create_message(message['type'], message['content']))

    def forward_message(self, message):
        recipient = message['recipient']
        for addr, client_socket in self.clients.items():
            if str(addr[1]) == recipient:
                try:
                    client_socket.send(create_message(MessageType.CHAT, message['content'], message['sender']).encode())
                    logger.info(f"Forwarded message from {message['sender']} to {recipient}")
                    break
                except Exception as e:
                    logger.error(f"Error forwarding message to {recipient}: {e}")

    def broadcast_message(self, message):
        for client_socket in self.clients.values():
            try:
                client_socket.send(message.encode())
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")

    def remove_client(self, addr):
        if addr in self.clients:
            self.clients[addr].close()
            del self.clients[addr]
            logger.info(f"Client {addr} disconnected")

    def shutdown(self):
        self.shutdown_event.set()
        for client_socket in self.clients.values():
            client_socket.close()
        self.clients.clear()
        logger.info("Server shut down")