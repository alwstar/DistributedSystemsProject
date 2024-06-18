print('\nWaiting to receive election message...\n')

data, address = ring_socket.recvfrom(buffer_size)
election_message = json.loads(data.decode())

if election_message['isLeader']:
    leader_uid = election_message['mid']
    # forward received election message to left neighbour
    participant = False
    ring_socket.sendto(json.dumps(election_message), neighbour)

if election_message['mid'] < my_uid and not participant:
    new_election_message = {
        "mid": my_uid,
        "isLeader": False
    }
    participant = True
    # send received election message to left neighbour
    ring_socket.sendto(json.dumps(new_election_message), neighbour)
elif election_message['mid'] > my_uid:
    # send received election message to left neighbour
    participant = True
    ring_socket.sendto(json.dumps(election_message), neighbour)
elif election_message['mid'] == my_uid:
    leader_uid = my_uid
    new_election_message = {
        "mid": my_uid,
        "isLeader": True
    }
    # send new election message to left neighbour
    participant = False
    ring_socket.sendto(json.dumps(new_election_message), neighbour)
