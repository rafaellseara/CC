# nettask_agent.py
import socket
import json

# Configurações para NetTask
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
AGENT_ID = "agent_001"

def send_registration_message():
    """Função para enviar mensagem de registo via NetTask (UDP)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    registration_message = json.dumps({"agent_id": AGENT_ID, "message_type": "register"})
    sock.sendto(registration_message.encode(), (UDP_IP, UDP_PORT))
    
    # Recebe a resposta do servidor
    data, _ = sock.recvfrom(1024)
    task_config = json.loads(data.decode())
    print("Configuração recebida do servidor:", task_config)
    sock.close()
    return task_config






'''
# nettask_agent.py
import socket
import json

# Configurações para NetTask
UDP_IP = "127.0.0.1"
UDP_PORT = 5005
AGENT_ID = "agent_001"

def send_registration_message():
    """Função para enviar mensagem de registo via NetTask (UDP)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    registration_message = json.dumps({"agent_id": AGENT_ID, "message_type": "register"})
    sock.sendto(registration_message.encode(), (UDP_IP, UDP_PORT))
    
    # Recebe a resposta do servidor
    data, _ = sock.recvfrom(1024)
    task_config = json.loads(data.decode())
    print("Configuração recebida do servidor:", task_config)
    sock.close()
    return task_config
'''