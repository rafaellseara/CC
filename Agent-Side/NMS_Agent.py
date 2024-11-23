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

    def register(self):
        register_message = {
            "message": "register",
        }
        self.udp_socket.sendto(json.dumps(register_message).encode(), (self.server_address, self.udp_port))
        print(f"Sent registration request to server at {self.server_address}")

        # Wait for response from server with assigned agent_id
        data, server = self.udp_socket.recvfrom(1024)
        response = json.loads(data.decode())
        
        if response.get("status") == "registered":
            self.agent_id = response.get("agent_id")
            print(f"Agent successfully registered with assigned agent_id: {self.agent_id}")
        else:
            print("Failed to register agent.")

    def receive_task(self):
        print(f"Listening for tasks from {self.server_address}")
        while True:
            # Listen for task instructions (e.g., metrics to collect)
            data, server = self.udp_socket.recvfrom(1024)
            task = json.loads(data.decode())
            print(f"Received task: {task}")
            
            # Send acknowledgment to the server
            self.send_task_ack(task.get("task_id"))
            
            # Start collecting metrics based on the task
            self.collect_metrics(task)

    def send_task_ack(self, task_id):
        if not task_id:
            print("No task ID found to send ACK.")
            return
        
        ack_message = {
            "message": "task_ack",
            "task_id": task_id,
            "agent_id": self.agent_id
        }
        self.udp_socket.sendto(json.dumps(ack_message).encode(), (self.server_address, self.udp_port))
        print(f"Sent ACK for task_id {task_id} to server.")

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


    def send_metrics(self, metrics):
        try:
            metrics_message = {
                "agent_id": self.agent_id,
                "metrics": metrics
            }
            self.udp_socket.sendto(json.dumps(metrics_message).encode(), (self.server_address, self.udp_port))
            print(f"[DEBUG] Metrics sent successfully: {metrics_message}")

            # Wait for ACK from server
            self.wait_for_ack()
        except Exception as e:
            print(f"[ERROR] Failed to send metrics: {e}")

    def wait_for_ack(self):
        try:
            self.udp_socket.settimeout(5)  # Set a timeout for ACK reception
            ack_data, _ = self.udp_socket.recvfrom(1024)
            ack_message = json.loads(ack_data.decode())
            if ack_message.get("message") == "metrics_ack" and ack_message.get("agent_id") == self.agent_id:
                print(f"[DEBUG] Received ACK from server for metrics: {ack_message}")
            else:
                print(f"[WARNING] Received unexpected ACK: {ack_message}")
        except socket.timeout:
            print("[ERROR] No ACK received from server within timeout period.")
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