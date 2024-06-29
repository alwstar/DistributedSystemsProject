from message import MessageType, create_message
from logger import setup_logger

logger = setup_logger("election")

class ElectionManager:
    def __init__(self, node_id, send_message_callback):
        self.node_id = node_id
        self.send_message = send_message_callback
        self.leader_id = None

    def start_election(self):
        logger.info(f"Node {self.node_id} starting election")
        election_message = create_message(MessageType.ELECTION, self.node_id)
        self.send_message(election_message)

    def handle_election_message(self, message):
        candidate_id = message["content"]
        if candidate_id > self.node_id:
            self.send_message(message)
        elif candidate_id < self.node_id:
            self.start_election()
        else:
            self.leader_id = self.node_id
            self.announce_leader()

    def announce_leader(self):
        leader_message = create_message(MessageType.LEADER, self.leader_id)
        self.send_message(leader_message)

    def handle_leader_message(self, message):
        self.leader_id = message["content"]
        logger.info(f"New leader elected: {self.leader_id}")