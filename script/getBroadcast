import ipaddress

def get_broadcast_address(ip_address, subnet_mask):
    network = ipaddress.IPv4Network(ip_address + '/' + subnet_mask, strict=False)
    return network.broadcast_address

# Replace 'ip_address' and 'subnet_mask' with your actual values
ip_address = '192.168.178.22'
subnet_mask = '255.255.255.0'

broadcast_address = get_broadcast_address(ip_address, subnet_mask)
print(f"Broadcast Address: {broadcast_address}")