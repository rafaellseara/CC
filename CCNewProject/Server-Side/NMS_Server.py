import socket
import json
import threading
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
        self.tcp_socket.listen(5)  # Listen for incoming TCP connections

        # Initialize storage system
        self.storage = Storage()

        # Dictionary to store registered agents
        self.agents = {}
        self.next_agent_id = 1  

    def start(self):
        print("Starting NMS_Server...")
        print(f"Server active in {self.udp_socket.getsockname()[0]} port {self.udp_port}")
        # Start a thread to handle UDP communication for receiving tasks and metrics
        threading.Thread(target=self.handle_udp).start()

        # Start a thread to handle TCP communication for receiving alerts
        threading.Thread(target=self.handle_tcp).start()

    def load_task_config(self, task_config_path):
        """ Load the task configuration from the task_config.json file. """
        task_config = TaskConfig.from_json(task_config_path)
        if task_config:
            print(f"Loaded TaskConfig: {task_config}")
            return task_config
        else:
            print("Failed to load task config.")
            return None

    def handle_udp(self):
        print(f"Listening for incoming UDP packets on port {self.udp_port}")
        while True:
            data, addr = self.udp_socket.recvfrom(1024)
            message = json.loads(data.decode())
            if message.get("message") == "register":
                # Register the agent
                self.register_agent(message, addr)
            elif "metrics" in message:
                # Process metrics from the agent
                self.process_metrics(message, addr)
            elif "task" in message:
                # Load the task configuration from a file and send it to the agent
                task_config = self.load_task_config("task_config.json")
                if task_config:
                    # Send task to agent
                    self.send_task_to_agent(message["agent_id"], task_config)

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

            # Store the alert using the storage system
            self.storage.store_alert(alert)

    def register_agent(self, message, addr):
        agent_id = f"agent_{self.next_agent_id}"  # Assign a new agent ID
        self.next_agent_id += 1
        self.agents[agent_id] = addr
        print(f"Agent {agent_id} registered at {addr}")

        # Store agent data
        self.storage.store_agent(agent_id, addr)

        # Send registration confirmation with assigned agent_id
        response = {"status": "registered", "agent_id": agent_id}
        self.udp_socket.sendto(json.dumps(response).encode(), addr)

    def process_metrics(self, message, addr):
        agent_id = message.get("agent_id")
        metrics = message.get("metrics")
        if agent_id and metrics:
            print(f"Received metrics from {agent_id}: {metrics}")

            # Store metrics data
            self.storage.store_metrics(agent_id, metrics)

    def send_task_to_agent(self, agent_id, task_config):
        """ Send the parsed task to the registered agent. """
        agent_address = self.agents.get(agent_id)
        if agent_address:
            task_data = {
                "task_id": task_config.task_id,
                "frequency": task_config.frequency,
                "devices": [device.device_id for device in task_config.devices]
            }
            # Send the task data to the agent (UDP)
            self.udp_socket.sendto(json.dumps(task_data).encode(), agent_address)
            print(f"Sent task {task_data} to agent {agent_id}")
        else:
            print(f"Agent {agent_id} not found.")


if __name__ == "__main__":
    udp_port = 5005
    tcp_port = 5070
    server = NMS_Server(udp_port, tcp_port)
    server.start()