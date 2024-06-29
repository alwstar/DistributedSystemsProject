import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="P2P Chat Application")
    parser.add_argument("mode", choices=["client", "server"], help="Run as client or server")
    parser.add_argument("-p", "--port", type=int, default=6000, help="TCP port (server mode)")
    parser.add_argument("-u", "--udp-port", type=int, default=5000, help="UDP discovery port")
    parser.add_argument("-b", "--buffer", type=int, default=1024, help="Buffer size")
    return parser.parse_args()