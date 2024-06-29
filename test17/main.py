from config import parse_args
from client import Client
from server import Server
from ui import UserInterface

def main():
    args = parse_args()
    
    if args.mode == "client":
        client = Client(args.udp_port, args.buffer)
        client.start()
        ui = UserInterface(client)
        ui.run()
    elif args.mode == "server":
        server = Server(args.port, args.udp_port, args.buffer)
        server.start()

if __name__ == "__main__":
    main()