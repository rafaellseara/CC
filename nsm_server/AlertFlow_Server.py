'''
# alertflow_server.py
import socket
import json

# Configurações do servidor AlertFlow
TCP_IP = "127.0.0.1"
TCP_PORT = 6006

def start_alertflow_server():
    """Inicia o servidor TCP para receber alertas dos agentes."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((TCP_IP, TCP_PORT))
    sock.listen(5)  # Permite múltiplas conexões
    print("AlertFlow Server iniciado...")

    while True:
        conn, addr = sock.accept()
        print(f"Conexão recebida de {addr}")
        data = conn.recv(1024)  # Recebe dados do agente
        alert_message = json.loads(data.decode())
        
        # Processa o alerta
        print(f"Alerta recebido: {alert_message}")
        
        # Envia confirmação de receção ao agente
        conn.sendall(b"ACK")
        conn.close()

# Teste inicial (este ficheiro deve ser executado a partir do nms_server.py)
if __name__ == "__main__":
    start_alertflow_server()
'''

'''
import socket

# Configurações do servidor
TCP_IP = "127.0.0.1"
TCP_PORT = 6006

# Cria o socket TCP
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((TCP_IP, TCP_PORT))
sock.listen(1)

print("NMS_Server à espera de conexões...")

conn, addr = sock.accept()
print(f"Conectado a: {addr}")

while True:
    data = conn.recv(1024)  # Recebe até 1024 bytes
    if not data:
        break
    print(f"Recebido: {data.decode()}")
    conn.sendall(b"ACK")  # Envia confirmação de receção

conn.close()
'''