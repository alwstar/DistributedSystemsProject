import subprocess
import time

def ping_device(ip):
    try:
        output = subprocess.check_output(["ping", "-n", "1", ip], stderr=subprocess.STDOUT, universal_newlines=True)
        if "TTL=" in output:
            print(f"{ip} is reachable")
        else:
            print(f"{ip} is not reachable")
    except subprocess.CalledProcessError:
        print(f"{ip} is not reachable")

def main():
    # Beispiel-Subnetz: 192.168.1.0/24
    base_ip = "192.168.1."
    start = 1
    end = 10

    while True:
        for i in range(start, end + 1):
            ip = f"{base_ip}{i}"
            ping_device(ip)
        time.sleep(5)  # Pause von 5 Sekunden vor dem nächsten Durchlauf

if __name__ == "__main__":
    main()
