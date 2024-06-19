class LeaderElection:
    def __init__(self, group_view):
        self.group_view = group_view
        self.leader = None

    def elect_leader(self):
        if not self.group_view:
            return None
        self.leader = min(self.group_view)
        return self.leader

# Usage in the server
group_view = ["192.168.0.2", "192.168.0.3", "192.168.0.4"]
election = LeaderElection(group_view)
leader = election.elect_leader()
print(f"Elected leader: {leader}")
