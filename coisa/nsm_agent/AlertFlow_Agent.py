import socket
import json

# Configuração do server AlertFlow
TCP_IP = "127.0.0.1"
TCP_PORT = 6006

def send_alert(alert_type, current_value, threshold, agent_id):
    alert_message = json.dumps({
        "agent_id": agent_id,
        "alert_type": alert_type,
        "current_value": current_value,
        "threshold": threshold
    })
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((TCP_IP, TCP_PORT))
            sock.sendall(alert_message.encode())
            response = sock.recv(1024).decode()
            print("Server response to alert:", response)
    except (ConnectionError, socket.error) as e:
        print("Error sending alert:", e)
