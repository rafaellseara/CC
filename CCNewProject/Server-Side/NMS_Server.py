import socket
import json
import threading
import time
from storage import Storage
from parse_json import TaskConfig

class NMS_Server:
    def __init__(self, udp_port, tcp_port):
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.host = socket.gethostname()

        # Set up UDP socket for NetTask communication
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind((socket.gethostbyname(self.host), self.udp_port))

        # Set up TCP socket for AlertFlow communication
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.bind((self.host, self.tcp_port))
        self.tcp_socket.listen(5)

        # Initialize storage system (in-memory)
        self.storage = Storage()

        # Timer and lock for task dispatch
        self.task_timer = None
        self.task_delay = 30  # seconds
        self.timer_lock = threading.Lock()

    def start(self):
        print("Starting NMS_Server...")
        print(f"Server active on {self.udp_socket.getsockname()[0]} port {self.udp_port}")

        # Start threads to handle UDP and TCP communication
        threading.Thread(target=self.handle_udp).start()
        threading.Thread(target=self.handle_tcp).start()

    def load_task_config(self, task_config_path):
        task_config = TaskConfig.from_json(task_config_path)
        if task_config:
            print(f"Loaded TaskConfig")
            return task_config
        else:
            print("Failed to load task config.")
            return None

    def handle_udp(self):
        # Load the task configuration from a file
        task_config = self.load_task_config("../task_config.json")

        print(f"Listening for incoming UDP packets on port {self.udp_port}")
        while True:
            data, addr = self.udp_socket.recvfrom(1024)
            message = json.loads(data.decode())
            
            if message.get("message") == "register":
                # Register the agent
                self.register_agent(message, addr)
                
                # Reset the task timer to wait 30 seconds before sending tasks
                with self.timer_lock:
                    if self.task_timer:
                        self.task_timer.cancel()  # Cancel any existing timer
                    self.task_timer = threading.Timer(self.task_delay, self.send_task_to_agents, [task_config])
                    self.task_timer.start()

            elif "metrics" in message:
                # Process metrics from the agent
                self.process_metrics(message)

    def handle_tcp(self):
        print(f"Listening for TCP connections on port {self.tcp_port}")
        while True:
            conn, addr = self.tcp_socket.accept()
            print(f"Accepted connection from {addr}")
            threading.Thread(target=self.handle_alert, args=(conn, addr)).start()

    def handle_alert(self, conn, addr):
        with conn:
            data = conn.recv(1024)  # Receive alert data
            alert = json.loads(data.decode())
            print(f"Received alert from {addr}: {alert}")

            # Store the alert in memory
            self.storage.store_alert(alert)

    def register_agent(self, message, addr):
        # Generate a unique agent ID (could be based on IP or incrementally)
        agent_id = str(len(self.storage.get_agents()) + 1)  # Simple unique ID generation

        # Store agent data in memory
        self.storage.store_agent(agent_id, addr)
        print(f"Agent {agent_id} registered at {addr}")

        # Send registration confirmation with the assigned agent ID
        response = {"status": "registered", "agent_id": agent_id}
        self.udp_socket.sendto(json.dumps(response).encode(), addr)

    def process_metrics(self, message):
        agent_id = message.get("agent_id")
        metrics = message.get("metrics")
        if agent_id and metrics:
            print(f"Received metrics from {agent_id}: {metrics}")

            # Store metrics data in memory
            self.storage.store_metrics(agent_id, metrics)

    def send_task_to_agents(self, task_config):
        # Loop through all devices in the task config and send task to each agent
        for device in task_config.devices:
            agent_address = self.storage.get_agent_address_by_device_id(device.device_id)
            
            if agent_address:
                task_data = {
                    "task_id": task_config.task_id,
                    "frequency": task_config.frequency,
                    "devices": [device.device_id for device in task_config.devices],
                    "metrics": device.metrics  # Assuming each device has its own metrics
                }
                
                # Send the task data to the agent (UDP)
                self.udp_socket.sendto(json.dumps(task_data).encode(), agent_address)
                print(f"Sent task {task_data} to agent {device.device_id}")
            else:
                print(f"Agent {device.device_id} not found.")


if __name__ == "__main__":
    udp_port = 5005
    tcp_port = 5070
    server = NMS_Server(udp_port, tcp_port)
    server.start()