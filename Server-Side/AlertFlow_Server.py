import socket
import threading
import json
import logging

class AlertFlow:
    def __init__(self, host, tcp_port, logger=None):
        self.host = host
        self.tcp_port = tcp_port
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind((self.host, self.tcp_port))
        self.tcp_socket.listen(5)  # Listen for up to 5 connections

        # Use the provided logger or the root logger
        self.logger = logger or logging.getLogger()

        self.logger.info(f"AlertFlow listening on {self.tcp_port}")

############################################################################################################################################################################################

    def handle_connection(self, conn, addr):
        """
        Handles an incoming TCP connection.
        """
        try:
            data = conn.recv(1024)
            alert = json.loads(data.decode())
            self.logger.error(f"Received alert from {addr}: {alert}")
        except Exception as e:
            self.logger.error(f"Failed while handling connection from {addr}: {e}")
        finally:
            conn.close()

############################################################################################################################################################################################

    def start(self):
        """
        Starts listening for incoming connections.
        """
        logging.info("AlertFlow server started.")
        while True:
            try:
                conn, addr = self.tcp_socket.accept()
                logging.info(f"Connection accepted from {addr}")
                threading.Thread(target=self.handle_connection, args=(conn, addr)).start()
            except Exception as e:
                logging.error(f"Failed to accept connection: {e}")

############################################################################################################################################################################################

    def close(self):
        """
        Closes the TCP socket.
        """
        self.tcp_socket.close()
        logging.info("AlertFlow socket closed")
