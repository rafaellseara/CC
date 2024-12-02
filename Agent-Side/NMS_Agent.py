import socket
import json
import time
import threading
from metrics import MetricCollector 

class NMS_Agent:
    def __init__(self, server_address, udp_port, tcp_port):
        self.server_address = server_address
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.agent_id = None 

        # Instantiate the MetricCollector
        self.metric_collector = MetricCollector()

        # UDP socket for NetTask
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # TCP socket for AlertFlow
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def register(self, retries=3, timeout=5):
        """
        Registers the agent with the server. Retransmits the registration message if no response is received.
        """
        register_message = {
            "message": "register",
        }
        for attempt in range(retries):
            try:
                # Send registration message
                self.udp_socket.sendto(json.dumps(register_message).encode(), (self.server_address, self.udp_port))
                print(f"[INFO] Sent registration request to server at {self.server_address} (Attempt {attempt + 1}/{retries})")

                # Wait for response from server
                self.udp_socket.settimeout(timeout)
                data, server = self.udp_socket.recvfrom(1024)
                response = json.loads(data.decode())

                # Process server response
                if response.get("status") == "registered":
                    self.agent_id = response.get("agent_id")
                    print(f"[INFO] Agent successfully registered with assigned agent_id: {self.agent_id}")
                    return True  # Registration successful
                else:
                    print("[WARNING] Received unexpected response during registration: ", response)
            except socket.timeout:
                print(f"[WARNING] No response from server. Retrying registration ({attempt + 1}/{retries})...")
            except Exception as e:
                print(f"[ERROR] Error during registration: {e}")
        print("[ERROR] Failed to register agent after multiple attempts.")
        return False  # Registration failed

    def receive_task(self):
        """
        Listens for tasks from the server and processes them when received.
        Runs indefinitely without a timeout.
        """
        # Ensure no timeout is set for the socket
        self.udp_socket.settimeout(None)

        while True:
            try:
                print(f"[INFO] Listening for tasks from {self.server_address}")
                data, server = self.udp_socket.recvfrom(1024)  # Blocking call, waits for data
                task = json.loads(data.decode())
                print(f"[INFO] Received task: {task}")
                self.send_task_ack(task)  # Send acknowledgment for the task
                self.collect_metrics(task)  # Process the received task
            except Exception as e:
                print(f"[ERROR] Error while receiving task: {e}")

    def send_task_ack(self, task):
        """
        Sends an acknowledgment for the received task.
        """
        ack_message = {
            "message": "task_ack",
            "agent_id": self.agent_id,
            "task_id": task["task_id"]  # Ensure only the task_id is included here
        }
        self.udp_socket.sendto(json.dumps(ack_message).encode(), (self.server_address, self.udp_port))
        print(f"[INFO] Sent ACK for task_id {task['task_id']} to server.")

    def collect_metrics(self, task):
        while True:
            try:
                print(f"[DEBUG] Collecting metrics for task ID: {task.get('task_id')}")

                # Collect all metrics, including CPU and RAM usage
                metrics = self.metric_collector.collect_all_metrics(task)
                print(f"[DEBUG] Metrics collected: {metrics}")

                # Send metrics to the server
                self.send_metrics(metrics)

                # Check for alert conditions
                self.check_alerts(metrics, task)

                # Sleep for the frequency defined in the task
                sleep_duration = task.get("frequency", 30)
                print(f"[DEBUG] Sleeping for {sleep_duration} seconds before next collection.")
                time.sleep(sleep_duration)
            except Exception as e:
                print(f"[ERROR] Error in collect_metrics: {e}")


    def send_metrics(self, metrics, retries=3, timeout=5):
        """
        Sends metrics to the server with retransmission if no ACK is received.
        """
        metrics_message = {
            "agent_id": self.agent_id,
            "metrics": metrics
        }
        for attempt in range(retries):
            try:
                # Send metrics
                self.udp_socket.sendto(json.dumps(metrics_message).encode(), (self.server_address, self.udp_port))
                print(f"[INFO] Metrics sent successfully: {metrics_message}")

                # Wait for acknowledgment
                self.udp_socket.settimeout(timeout)
                ack_data, _ = self.udp_socket.recvfrom(1024)
                ack = json.loads(ack_data.decode())
                if ack.get("message") == "metrics_ack" and ack.get("agent_id") == self.agent_id:
                    print(f"[INFO] Received metrics acknowledgment from server.")
                    return True  # Stop retrying if ACK is received
            except socket.timeout:
                print(f"[WARNING] No metrics ACK received, retrying ({attempt + 1}/{retries})...")
            except Exception as e:
                print(f"[ERROR] Error while sending metrics: {e}")
        print(f"[ERROR] Failed to send metrics after {retries} attempts.")
        return False

    def wait_for_ack(self, expected_ack_type):
        """
        Waits for an acknowledgment of a specific type from the server.
        """
        try:
            self.udp_socket.settimeout(5)  # Set a timeout for ACK reception
            ack_data, _ = self.udp_socket.recvfrom(1024)
            ack_message = json.loads(ack_data.decode())
            if ack_message.get("message") == expected_ack_type and ack_message.get("agent_id") == self.agent_id:
                print(f"[DEBUG] Received {expected_ack_type} ACK from server: {ack_message}")
            else:
                print(f"[WARNING] Received unexpected ACK: {ack_message}")
        except socket.timeout:
            print(f"[ERROR] No {expected_ack_type} ACK received from server within timeout period.")
        finally:
            self.udp_socket.settimeout(None)  # Reset timeout to default


    def send_alert(self, alert_message):
        try:
            self.tcp_socket.connect(self.server_address)
            self.tcp_socket.sendall(alert_message.encode())
            print(f"Sent alert to server: {alert_message}")
            self.tcp_socket.close()
        except Exception as e:
            print(f"Failed to send alert: {e}")

    def check_alerts(self, metrics, task):
        alert_conditions = task.get("alertflow_conditions", {})

        # Check CPU usage
        if metrics["cpu_usage"] > alert_conditions.get("cpu_usage", float('inf')):
            alert_message = json.dumps({
                "alert": "cpu_usage",
                "value": metrics["cpu_usage"],
                "agent_id": self.agent_id,
                "threshold": alert_conditions["cpu_usage"]
            })
            self.send_alert(alert_message)

        # Check RAM usage
        if metrics["ram_usage"] > alert_conditions.get("ram_usage", float('inf')):
            alert_message = json.dumps({
                "alert": "ram_usage",
                "value": metrics["ram_usage"],
                "agent_id": self.agent_id,
                "threshold": alert_conditions["ram_usage"]
            })
            self.send_alert(alert_message)

    def start(self):
        self.register()

        # Start a separate thread for receiving tasks from the server
        task_thread = threading.Thread(target=self.receive_task)
        task_thread.start()

if __name__ == "__main__":
    server_address = "127.0.1.1" 
    udp_port = 5005
    tcp_port = 5070
    agent = NMS_Agent(server_address, udp_port, tcp_port)
    agent.start()