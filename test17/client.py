from network import NetworkManager
from election import ElectionManager
from message import MessageType, create_message
from logger import setup_logger

logger = setup_logger("client")

class Client:
    def __init__(self, udp_port, buffer_size):
        self.network = NetworkManager(udp_port, buffer_size)
        self.node_id = None
        self.election = None

    def start(self):
        server_ip, server_port = self.network.discover_server()
        self.node_id = self.network.connect_to_server(server_ip, server_port)
        self.election = ElectionManager(self.node_id, self.network.send_message)
        threading.Thread(target=self.network.receive_messages, args=(self.handle_message,), daemon=True).start()

    def handle_message(self, message):
        if message['type'] == MessageType.CHAT:
            logger.info(f"Received chat message: {message['content']}")
        elif message['type'] == MessageType.ELECTION:
            self.election.handle_election_message(message)
        elif message['type'] == MessageType.LEADER:
            self.election.handle_leader_message(message)
        elif message['type'] == MessageType.HEARTBEAT:
            logger.debug("Received heartbeat from server")

    def send_chat_message(self, recipient, content):
        message = create_message(MessageType.CHAT, content, sender=self.node_id, recipient=recipient)
        self.network.send_message(message)

    def shutdown(self):
        self.network.shutdown()