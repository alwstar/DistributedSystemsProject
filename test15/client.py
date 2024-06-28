import socket
import threading
import pickle
import ports
from multicast_sender import send_multicast_message

def receive_messages(sock):
    """
    Receives messages from the server and prints them out.
    """
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                print("Disconnected from server")
                break
            print(f"Message from server: {data.decode()}")
        except Exception as e:
            print(f"Error receiving message: {e}")
            break

def send_messages(sock):
    """
    Sends messages entered by the user to the server.
    """
    try:
        while True:
            message = input("Enter message: ")
            if message:
                sock.sendall(message.encode())
    except Exception as e:
        print(f"Error sending message: {e}")

def main():
    host = input("Enter the server IP address: ")
    port = ports.SERVER_PORT_FOR_CLIENTS

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))
        threading.Thread(target=receive_messages, args=(sock,)).start()
        send_messages(sock)

if __name__ == '__main__':
    main()
