import socket
import json

# Configuration for NetTask
UDP_IP = "127.0.0.1"
UDP_PORT = 5005

def send_registration_message(agent_id):
    """Send a registration message to NMS_Server via UDP."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    registration_message = json.dumps({"agent_id": agent_id, "message_type": "register"})
    sock.sendto(registration_message.encode(), (UDP_IP, UDP_PORT))
    
    # Receive configuration from the server
    data, _ = sock.recvfrom(1024)
    task_config = json.loads(data.decode())
    print("Configuration received from server:", task_config)
    print("Registration confirmed by NMS_Server.")
    sock.close()
    return task_config
