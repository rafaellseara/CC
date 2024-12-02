import socket
import threading
import json

class AlertFlow:
    def __init__(self, host, tcp_port):
        self.host = host
        self.tcp_port = tcp_port
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind((self.host, self.tcp_port))
        self.tcp_socket.listen(5)  # Listen for up to 5 connections
        print(f"[INFO] AlertFlow listening on {self.tcp_port}")

    def handle_connection(self, conn, addr):
        """
        Handles an incoming TCP connection.
        """
        try:
            data = conn.recv(1024)
            alert = json.loads(data.decode())
            print(f"[INFO] Received alert from {addr}: {alert}")

            # Optionally, send an acknowledgment back
            ack_message = {"status": "ack", "alert_received": True}
            conn.sendall(json.dumps(ack_message).encode())
            print(f"[INFO] Sent ACK to {addr}")
        except Exception as e:
            print(f"[ERROR] Error handling connection from {addr}: {e}")
        finally:
            conn.close()

    def start(self):
        """
        Starts listening for incoming connections.
        """
        print("[INFO] AlertFlow server started.")
        while True:
            try:
                conn, addr = self.tcp_socket.accept()
                print(f"[INFO] Connection accepted from {addr}")
                threading.Thread(target=self.handle_connection, args=(conn, addr)).start()
            except Exception as e:
                print(f"[ERROR] Failed to accept connection: {e}")

    def close(self):
        """
        Closes the TCP socket.
        """
        self.tcp_socket.close()
        print("[INFO] AlertFlow socket closed.")
