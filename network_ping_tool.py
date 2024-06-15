
import os
import platform
import subprocess
from ping3 import ping, verbose_ping

def ping_device(ip):
    response = ping(ip)
    if response is not None:
        print(f"{ip} is reachable")
    else:
        print(f"{ip} is not reachable")

def main():
    # Beispiel-Subnetz: 192.168.1.0/24
    base_ip = "192.168.1."
    start = 1
    end = 254

    for i in range(start, end + 1):
        ip = f"{base_ip}{i}"
        ping_device(ip)

if __name__ == "__main__":
    main()
