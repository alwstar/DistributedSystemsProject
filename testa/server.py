import socket
import threading
import time
import sys
import xml.etree.ElementTree as ET

# Constants
UDP_PORT = 42000
BUFFER_SIZE = 1024
TCP_PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 6000

# Global variables
connectedUsers = {}  # Dictionary to store user information (socket, address)
leader = None  # Current leader
isActive = True  # Server active state
discussionGroups = {}  # Dictionary to store discussion groups and their members

# Shutdown event
shutdownEvent = threading.Event()

def initiateLeaderElection():
    global leader
    if connectedUsers:
        maxId = max(connectedUsers, key=lambda addr: addr[1])
        leader = maxId
        announceLeader(leader)
    else:
        leader = None
        print("No users connected. Cannot initiate leader election.")

def broadcastServerPresence():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udpSocket:
        udpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        while isActive:
            message = f"ServerAvailable:{TCP_PORT}".encode()
            udpSocket.sendto(message, ('<broadcast>', UDP_PORT))
            time.sleep(10)

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

def userConnectionManager(userSocket, addr):
    global connectedUsers, leader
    while not shutdownEvent.is_set():
        try:
            message = userSocket.recv(BUFFER_SIZE)
            if not message:
                break

            messageType, data = parseXmlMessage(message)

            if messageType == "election":
                processElectionMessage(userSocket, addr, data)
            elif messageType == "chatroom":
                processChatroomMessage(userSocket, addr, data)
            else:
                print(f"Unknown message type received: {messageType}")

        except Exception as e:
            print(f"Error handling user {addr}: {e}")
            break

    userSocket.close()
    print(f"Connection with {addr} closed")
    if addr in connectedUsers:
        del connectedUsers[addr]
        for group in discussionGroups.values():
            if addr in group:
                group.remove(addr)
        if addr == leader:
            print("Leader has disconnected. Initiating new leader election.")
            initiateLeaderElection()

def processElectionMessage(userSocket, addr, data):
    global leader
    senderId = data['mid']
    isLeader = data['isLeader'] == 'true'

    if isLeader:
        leader = (addr[0], int(senderId))
        announceLeader(leader)
    else:
        nextUser = getNextUser(addr)
        if nextUser:
            connectedUsers[nextUser].send(createXmlMessage("election", mid=senderId, isLeader="false"))

def getNextUser(currentAddr):
    userList = list(connectedUsers.keys())
    if currentAddr in userList:
        currentIndex = userList.index(currentAddr)
        nextIndex = (currentIndex + 1) % len(userList)
        return userList[nextIndex]
    return None

def announceLeader(leaderAddr):
    leaderAnnouncement = createXmlMessage("leader_announcement", leader_ip=leaderAddr[0], leader_port=leaderAddr[1])
    for userSocket in connectedUsers.values():
        userSocket.send(leaderAnnouncement)
    print(f"Leader is {leaderAddr}")

def processChatroomMessage(userSocket, addr, data):
    action = data['action']
    chatroom = data['chatroom']

    if action == "join":
        if chatroom not in discussionGroups:
            discussionGroups[chatroom] = set()
        discussionGroups[chatroom].add(addr)
        announceUserJoined(chatroom, addr)
    elif action == "leave":
        if chatroom in discussionGroups and addr in discussionGroups[chatroom]:
            discussionGroups[chatroom].remove(addr)
            announceUserLeft(chatroom, addr)
    elif action == "message":
        if chatroom in discussionGroups and addr in discussionGroups[chatroom]:
            broadcastChatroomMessage(chatroom, addr, data['content'])

def announceUserJoined(chatroom, addr):
    announcement = createXmlMessage("chatroom_update", action="joined", chatroom=chatroom, user_ip=addr[0], user_port=addr[1])
    for userAddr in discussionGroups[chatroom]:
        if userAddr in connectedUsers:
            connectedUsers[userAddr].send(announcement)

def announceUserLeft(chatroom, addr):
    announcement = createXmlMessage("chatroom_update", action="left", chatroom=chatroom, user_ip=addr[0], user_port=addr[1])
    for userAddr in discussionGroups[chatroom]:
        if userAddr in connectedUsers:
            connectedUsers[userAddr].send(announcement)

def broadcastChatroomMessage(chatroom, senderAddr, content):
    message = createXmlMessage("chatroom_message", chatroom=chatroom, sender_ip=senderAddr[0], sender_port=senderAddr[1], content=content)
    for userAddr in discussionGroups[chatroom]:
        if userAddr in connectedUsers:
            connectedUsers[userAddr].send(message)

def terminateServer(tcpSocket):
    global isActive
    isActive = False
    shutdownEvent.set()

    for userSocket in connectedUsers.values():
        try:
            userSocket.close()
        except Exception as e:
            print(f"Error closing user connection: {e}")

    connectedUsers.clear()
    discussionGroups.clear()
    tcpSocket.close()
    print("Server has been terminated.")

def displayConnectedUsers():
    if connectedUsers:
        print("Connected users:")
        for addr in connectedUsers.keys():
            print(f"User at {addr}")
    else:
        print("No users connected.")

def main():
    global isActive, leader

    tcpPort = TCP_PORT
    if len(sys.argv) > 1:
        try:
            tcpPort = int(sys.argv[1])
        except ValueError:
            print("Invalid port number. Using default port:", TCP_PORT)

    broadcastThread = threading.Thread(target=broadcastServerPresence)
    broadcastThread.start()

    tcpSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcpSocket.bind(('', tcpPort))
    tcpSocket.listen()
    print(f"TCP server listening on port {tcpPort}")

    def manageConnections(tcpSocket):
        global connectedUsers, isActive

        while isActive:
            try:
                userSocket, addr = tcpSocket.accept()
                connectedUsers[addr] = userSocket
                print(f"Connected to {addr}")
                threading.Thread(target=userConnectionManager, args=(userSocket, addr)).start()

                if leader is None:
                    initiateLeaderElection()

            except Exception as e:
                print(f"Error in connection management: {e}")

        tcpSocket.close()

    connectionThread = threading.Thread(target=manageConnections, args=(tcpSocket,))
    connectionThread.start()

    while isActive:
        cmd = input("\nSelect an option\n1: Display current leader\n2: Show users\n3: Terminate server\n")
        if cmd == '3':
            terminateServer(tcpSocket)
            break
        elif cmd == '2':
            displayConnectedUsers()
        elif cmd == '1':
            if leader:
                print(f"Current leader is: {leader}")
            else:
                print("No leader has been elected yet.")
        else:
            print("Invalid command.")

    connectionThread.join()
    broadcastThread.join()

if __name__ == "__main__":
    main()