import threading
from logger import setup_logger

logger = setup_logger("ui")

class UserInterface:
    def __init__(self, client):
        self.client = client

    def run(self):
        while True:
            try:
                command = input("Enter command (m: send message, e: start election, q: quit): ").strip().lower()
                if command == 'm':
                    self.send_message()
                elif command == 'e':
                    self.client.election.start_election()
                elif command == 'q':
                    self.quit()
                    break
                else:
                    logger.warning("Invalid command. Please try again.")
            except KeyboardInterrupt:
                self.quit()
                break

    def send_message(self):
        recipient = input("Enter recipient's node ID: ")
        content = input("Enter your message: ")
        self.client.send_chat_message(recipient, content)

    def quit(self):
        logger.info("Shutting down client...")
        self.client.shutdown()