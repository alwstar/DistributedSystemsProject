import subprocess
import time

# Start server.py
server_process = subprocess.Popen(['python', 'server.py'])
print("Server started")

# Wait for a few seconds to ensure the server is up and running
time.sleep(5)

# Start fault_tolerance.py
fault_tolerance_process = subprocess.Popen(['python', 'fault_tolerance.py'])
print("Fault tolerance started")

# Start leader_election.py
leader_election_process = subprocess.Popen(['python', 'leader_election.py'])
print("Leader election started")

# Wait for the processes to complete (optional)
try:
    server_process.wait()
    fault_tolerance_process.wait()
    leader_election_process.wait()
except KeyboardInterrupt:
    # Handle cleanup here if necessary
    print("Terminating processes...")
    server_process.terminate()
    fault_tolerance_process.terminate()
    leader_election_process.terminate()
