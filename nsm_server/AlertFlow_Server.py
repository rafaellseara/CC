import socket
import json

# Configuração do server do AlertFlow
TCP_IP = "127.0.0.1"
TCP_PORT = 6006

def start_alertflow_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((TCP_IP, TCP_PORT))
    sock.listen(5)
    print("AlertFlow Server started...")

    while True:
        conn, addr = sock.accept()
        print(f"Connection received from {addr}")
        data = conn.recv(1024) 
        if data:
            try:
                alert_message = json.loads(data.decode())
                print(f"Alert received from {alert_message['agent_id']}: {alert_message}")
            except json.JSONDecodeError:
                print("Error decoding alert message:", data)

        conn.sendall(b"ACK")
        conn.close()

if __name__ == "__main__":
    start_alertflow_server()
