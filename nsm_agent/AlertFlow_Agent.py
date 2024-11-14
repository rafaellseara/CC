'''
# alertflow_agent.py
import socket
import json

# Configurações para AlertFlow
TCP_IP = "127.0.0.1"
TCP_PORT = 6006

def send_alert(alert_type, current_value, threshold, agent_id="agent_001"):
    """Função para enviar alertas via AlertFlow (TCP)."""
    alert_message = json.dumps({
        "agent_id": agent_id,
        "alert_type": alert_type,
        "current_value": current_value,
        "threshold": threshold
    })
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((TCP_IP, TCP_PORT))
    sock.sendall(alert_message.encode())
    response = sock.recv(1024).decode()
    print("Resposta do servidor ao alerta:", response)
    sock.close()
'''








'''
import socket

# Configurações do agente
TCP_IP = "127.0.0.1"
TCP_PORT = 6006

# Cria o socket TCP
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((TCP_IP, TCP_PORT))

# Mensagem de alerta
message = "Alerta: CPU acima do limite."

# Envia a mensagem de alerta
sock.sendall(message.encode())

# Recebe confirmação do servidor
data = sock.recv(1024)
print("Resposta do servidor:", data.decode())

sock.close()
'''