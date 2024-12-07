import socket
import json
import logging

class NetTask:
    def __init__(self, host, udp_port, logger=None):
        self.host = host
        self.udp_port = udp_port
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind((self.host, self.udp_port))
        
        # Use the provided logger or the root logger
        self.logger = logger or logging.getLogger()

        self.logger.info(f"NetTask listening on {self.udp_port}")

        self.registered_agents = {}

    def receive_message(self, timeout=None):
        """
        Receives a message over UDP with optional timeout.
        
        :param timeout: Timeout in seconds (None means no timeout).
        :return: message and address if received, otherwise (None, None).
        """
        try:
            if timeout is not None:
                self.udp_socket.settimeout(timeout)  # Set timeout for receiving the message

            data, addr = self.udp_socket.recvfrom(1024)
            message = json.loads(data.decode())
            return message, addr
        except socket.timeout:
            self.logger.warning(f"Timeout reached while waiting for a message.")
            return None, None
        except Exception as e:
            self.logger.error(f"Failed to receive UDP message: {e}")
            return None, None

    def send_message(self, message, address, agent_id=None):
        """
        Sends a message over UDP.
        """
        try:
            self.udp_socket.sendto(json.dumps(message).encode(), address)
            self.logger.info(f"Message sent to {address}")
        except Exception as e:
            self.logger.error(f"Failed to send UDP message to {address}: {e}")

    def send_with_retransmission(self, message, address, ack_message_type, retries=3, timeout=5):
        """
        Sends a message with retransmission if no ACK is received.
        """
        for attempt in range(retries):
            try:
                self.send_message(message, address)
                self.logger.info(f"Sent message to {address}, waiting for ACK ({ack_message_type}).")

                # Start the timeout only after sending the message
                self.udp_socket.settimeout(timeout)

                # Wait for ACK
                ack_data, _ = self.udp_socket.recvfrom(1024)
                ack = json.loads(ack_data.decode())
                if ack.get("message") == ack_message_type and ack.get("agent_id") == message.get("agent_id"):
                    self.logger.info(f"Received ACK for {ack_message_type} from agent {ack.get('agent_id')}")
                    return True  # Stop retrying once ACK is received
            except socket.timeout:
                self.logger.warning(f"No ACK received for {ack_message_type}, retrying ({attempt + 1}/{retries})...")
            except Exception as e:
                self.logger.error(f"Failed retransmission: {e}")
        self.logger.error(f"Failed to receive ACK for {ack_message_type} after {retries} attempts")
        return False

    def close(self):
        """
        Closes the UDP socket.
        """
        self.udp_socket.close()
        self.logger.info("NetTask socket closed")