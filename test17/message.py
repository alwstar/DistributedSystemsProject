import json

class MessageType:
    CHAT = "CHAT"
    ELECTION = "ELECTION"
    LEADER = "LEADER"
    HEARTBEAT = "HEARTBEAT"

def create_message(msg_type, content, sender=None, recipient=None):
    return json.dumps({
        "type": msg_type,
        "content": content,
        "sender": sender,
        "recipient": recipient
    })

def parse_message(message):
    return json.loads(message)