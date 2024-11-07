import socket

def register_agent(server_ip, server_port, agent_id):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        message = f"REGISTER {agent_id}"
        sock.sendto(message.encode(), (server_ip, server_port))
