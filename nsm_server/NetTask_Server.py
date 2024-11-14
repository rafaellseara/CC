# nettask_server.py
import socket
import json

# Configurações do servidor NetTask
UDP_IP = "127.0.0.1"
UDP_PORT = 5005

def start_nettask_server(task_config):
    """Inicia o servidor UDP para receber registos dos agentes e enviar configurações."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((UDP_IP, UDP_PORT))
    print("NetTask Server iniciado...")

    while True:
        data, addr = sock.recvfrom(1024)  # Recebe dados de um agente
        message = json.loads(data.decode())
        print(f"Mensagem recebida de {addr}: {message}")

        if message.get("message_type") == "register":
            # Envia a configuração de tarefas para o agente
            response = json.dumps(task_config)
            sock.sendto(response.encode(), addr)
            print(f"Configuração enviada para {addr}")

# Teste inicial (este ficheiro deve ser executado a partir do nms_server.py)
if __name__ == "__main__":
    sample_task_config = {
        "frequency": 20,
        "devices": [{"device_id": "r1", "alertflow_conditions": {"cpu_usage": 80, "ram_usage": 90}}]
    }
    start_nettask_server(sample_task_config)


'''
import socket

# Configurações do servidor
UDP_IP = "127.0.0.1"
UDP_PORT = 5005

# Cria o socket UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((UDP_IP, UDP_PORT))

print("NMS_Server à espera de dados...")

while True:
    data, addr = sock.recvfrom(1024)  # Recebe até 1024 bytes
    print(f"Recebido de {addr}: {data.decode()}")
    sock.sendto(b"ACK", addr)  # Envia confirmação de receção
'''