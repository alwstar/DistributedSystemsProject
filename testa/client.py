import socket
import threading
import sys
import time
import xml.etree.ElementTree as ET

# Constants
SERVER_UDP_PORT = 42000
BUFFER_SIZE = 1024

# Global variables
shutdownEvent = threading.Event()
myId = None
currentChatroom = None
isParticipant = False
leaderId = None

def createXmlMessage(messageType, **kwargs):
    root = ET.Element("message")
    ET.SubElement(root, "type").text = messageType
    for key, value in kwargs.items():
        ET.SubElement(root, key).text = str(value)
    return ET.tostring(root)

def parseXmlMessage(xmlString):
    root = ET.fromstring(xmlString)
    messageType = root.find("type").text
    data = {child.tag: child.text for child in root if child.tag != "type"}
    return messageType, data

def locateServer():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udpSocket:
        udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        udpSocket.bind(('', SERVER_UDP_PORT))

        while True:
            message, serverAddr = udpSocket.recvfrom(BUFFER_SIZE)
            serverIp = serverAddr[0]
            _, serverTcpPort = message.decode().split(':')
            print(f"Located server at {serverIp} on port {serverTcpPort}")
            return serverIp, int(serverTcpPort)

def sendMessageToServer(tcpSocket, messageType, **kwargs):
    try:
        message = createXmlMessage(messageType, **kwargs)
        tcpSocket.send(message)
    except ConnectionError:
        print("Connection to the server lost.")
        tcpSocket.close()

def receiveMessages(tcpSocket):
    global myId, currentChatroom, isParticipant, leaderId
    while not shutdownEvent.is_set():
        try:
            message = tcpSocket.recv(BUFFER_SIZE)
            if not message:
                break

            messageType, data = parseXmlMessage(message)

            if messageType == "leader_announcement":
                leaderId = int(data['leader_port'])
                print(f"New leader is {data['leader_ip']}:{leaderId}")
                isParticipant = False
            elif messageType == "election":
                processElectionMessage(tcpSocket, data)
            elif messageType == "chatroom_update":
                print(f"User {data['user_ip']}:{data['user_port']} has {data['action']} chatroom {data['chatroom']}")
            elif messageType == "chatroom_message":
                print(f"[{data['chatroom']}] {data['sender_ip']}:{data['sender_port']}: {data['content']}")
            else:
                print(f"Received unknown message type: {messageType}")

        except Exception as e:
            print(f"Error receiving message: {e}")
            break

    if not shutdownEvent.is_set():
        print("Connection to the server lost. Attempting to reconnect...")
        reestablishConnection()

def processElectionMessage(tcpSocket, data):
    global myId, isParticipant, leaderId
    senderId = int(data['mid'])
    isLeader = data['isLeader'] == 'true'

    if isLeader:
        leaderId = senderId
        isParticipant = False
        print(f"New leader elected: {leaderId}")
    elif not isParticipant:
        if senderId < myId:
            isParticipant = True
            sendMessageToServer(tcpSocket, "election", mid=str(myId), isLeader="false")
        else:
            sendMessageToServer(tcpSocket, "election", mid=str(senderId), isLeader="false")
    elif senderId == myId:
        leaderId = myId
        isParticipant = False
        sendMessageToServer(tcpSocket, "election", mid=str(myId), isLeader="true")
    else:
        sendMessageToServer(tcpSocket, "election", mid=str(senderId), isLeader="false")

def reestablishConnection():
    global tcpSocket
    while not shutdownEvent.is_set():
        try:
            serverIp, serverTcpPort = locateServer()
            newSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            newSocket.connect((serverIp, serverTcpPort))
            tcpSocket = newSocket
            print("Reconnected to the server.")
            threading.Thread(target=receiveMessages, args=(tcpSocket,)).start()
            if currentChatroom:
                sendMessageToServer(tcpSocket, "chatroom", action="join", chatroom=currentChatroom)
            return
        except Exception as e:
            print(f"Failed to reconnect: {e}")
            time.sleep(5)

def main():
    global myId, tcpSocket, currentChatroom

    try:
        serverIp, serverTcpPort = locateServer()
        tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcpSocket.connect((serverIp, serverTcpPort))
        print("Connected to the server.")

        myId = tcpSocket.getsockname()[1]
        print(f"My ID is {myId}")

        threading.Thread(target=receiveMessages, args=(tcpSocket,)).start()

        # Initiate the election process
        sendMessageToServer(tcpSocket, "election", mid=str(myId), isLeader="false")

        while True:
            print("\nChoose an option:")
            print("1. Enter a chatroom")
            print("2. Exit current chatroom")
            print("3. Send a message in current chatroom")
            print("4. Start leader election")
            print("5. Disconnect client")
            choice = input("Enter your choice (1-5): ")

            if choice == '1':
                chatroom = input("Enter chatroom name: ")
                currentChatroom = chatroom
                sendMessageToServer(tcpSocket, "chatroom", action="join", chatroom=chatroom)
            elif choice == '2':
                if currentChatroom:
                    sendMessageToServer(tcpSocket, "chatroom", action="leave", chatroom=currentChatroom)
                    currentChatroom = None
                else:
                    print("You are not in any chatroom.")
            elif choice == '3':
                if currentChatroom:
                    message = input("Type your message: ")
                    sendMessageToServer(tcpSocket, "chatroom", action="message", chatroom=currentChatroom, content=message)
                else:
                    print("You are not in any chatroom.")
            elif choice == '4':
                sendMessageToServer(tcpSocket, "election", mid=str(myId), isLeader="false")
                print("Started leader election.")
            elif choice == '5':
                print("Disconnecting client...")
                shutdownEvent.set()
                tcpSocket.close()
                break
            else:
                print("Invalid choice. Please try again.")

    except Exception as e:
        print(f"An error occurred: {e}")

    print("Client disconnected.")

if __name__ == "__main__":
    main()