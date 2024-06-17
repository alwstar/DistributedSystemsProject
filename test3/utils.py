import uuid
import json

def generate_uuid():
    return str(uuid.uuid4())

def encode_message(message):
    return json.dumps(message).encode()

def decode_message(encoded_message):
    return json.loads(encoded_message.decode())
