import socket
import json

# Configurações do servidor NetTask
UDP_IP = "127.0.0.1"
UDP_PORT = 5005

def start_nettask_server(task_config):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print("NetTask Server iniciado...")

    while True:
        data, addr = sock.recvfrom(1024)  # Recebe dados de um agente
        message = json.loads(data.decode())
        if message.get("message_type") == "register":
            response = json.dumps(task_config)
            sock.sendto(response.encode(), addr)
            print(f"Configuração enviada para {addr}")
        elif "cpu_usage" in message and "ram_usage" in message:
            print(f"Metric received from {message['agent_id']}: CPU={message['cpu_usage']}%, RAM={message['ram_usage']}%")
            sock.sendto(b"ACK", addr)  # Send acknowledgment back to agent

if __name__ == "__main__":
    sample_task_config = {
        "frequency": 20,
        "devices": [{"device_id": "r1", "alertflow_conditions": {"cpu_usage": 80, "ram_usage": 90}}]
    }
    start_nettask_server(sample_task_config)
