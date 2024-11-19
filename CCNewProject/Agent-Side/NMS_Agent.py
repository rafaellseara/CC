import socket
import json
import time
import threading
from metrics import MetricCollector 

class NMS_Agent:
    def __init__(self, server_address, udp_port, tcp_port, agent_id):
        self.server_address = server_address
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.agent_id = agent_id

        # Instantiate the MetricCollector
        self.metric_collector = MetricCollector()

        # UDP socket for NetTask
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # TCP socket for AlertFlow
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def register(self):
        register_message = {
            "message": "register",
            "agent_id": self.agent_id
        }
        self.udp_socket.sendto(json.dumps(register_message).encode(), self.server_address)
        print(f"Sent registration to server at {self.server_address}")

        # Wait for confirmation from server
        data, server = self.udp_socket.recvfrom(1024)
        response = json.loads(data.decode())
        if response.get("status") == "registered":
            print(f"Agent {self.agent_id} successfully registered.")
        else:
            print(f"Failed to register Agent {self.agent_id}.")

    def receive_task(self):
        print(f"Listening for tasks from {self.server_address}")
        while True:
            # Listen for task instructions (e.g., metrics to collect)
            data, server = self.udp_socket.recvfrom(1024)
            task = json.loads(data.decode())
            print(f"Received task: {task}")
            # Here we can start collecting the metrics based on the task
            self.collect_metrics(task)

    def collect_metrics(self, task):
        while True:
            # Use the MetricCollector to gather all metrics
            metrics = self.metric_collector.collect_all_metrics()
            print(f"Collected metrics: {metrics}")

            # Send metrics back to the server
            self.send_metrics(metrics)

            # Check for critical conditions and send alerts if needed
            self.check_alerts(metrics, task)

            # Sleep for the frequency defined in the task (if available)
            time.sleep(task.get("frequency", 30))

    def send_metrics(self, metrics):
        metrics_message = json.dumps(metrics)
        self.udp_socket.sendto(metrics_message.encode(), self.server_address)
        print(f"Sent metrics to server: {metrics}")

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
