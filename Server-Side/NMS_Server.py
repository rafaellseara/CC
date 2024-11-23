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
        self.task_delay = 20  # seconds
        self.timer_lock = threading.Lock()

    def start(self):
        print("Starting NMS_Server...")
        print(f"Server active on {self.udp_socket.getsockname()[0]} port {self.udp_port}")

        # Start threads to handle UDP and TCP communication
        threading.Thread(target=self.handle_udp).start()
        threading.Thread(target=self.handle_tcp).start()

    def load_task_config(self, task_config_path):
        try:
            task_config = TaskConfig.from_json(task_config_path)
            if task_config:
                print(f"Loaded TaskConfig")
                return task_config
            else:
                print("Failed to load task config.")
                return None
        except Exception as e:
            print(f"Error loading task config: {e}")
            return None

    def handle_udp(self):
        task_config = self.load_task_config("task_config.json")
        print(f"Listening for incoming UDP packets on port {self.udp_port}")
        while True:
            try:
                data, addr = self.udp_socket.recvfrom(1024)
                message = json.loads(data.decode())
                self.process_udp_message(message, addr, task_config)
            except Exception as e:
                print(f"Error in UDP handling: {e}")

    def process_udp_message(self, message, addr, task_config):
        if message.get("message") == "register":
            self.register_agent(message, addr)
            with self.timer_lock:
                if self.task_timer:
                    self.task_timer.cancel()
                self.task_timer = threading.Timer(self.task_delay, self.send_task_to_agents, [task_config])
                self.task_timer.start()
        elif message.get("message") == "task_ack":
            self.process_task_ack(message)
        elif "metrics" in message:
            self.process_metrics(message,addr)

    def process_task_ack(self, message):
        task_id = message.get("task_id")
        agent_id = message.get("agent_id")
        print(f"Received ACK for task {task_id} from agent {agent_id}")

    def handle_tcp(self):
        print(f"Listening for TCP connections on port {self.tcp_port}")
        while True:
            try:
                conn, addr = self.tcp_socket.accept()
                threading.Thread(target=self.handle_alert, args=(conn, addr)).start()
            except Exception as e:
                print(f"Error in TCP handling: {e}")

    def handle_alert(self, conn, addr):
        with conn:
            try:
                data = conn.recv(1024)
                alert = json.loads(data.decode())
                print(f"Received alert from {addr}: {alert}")
                self.storage.store_alert(alert)
            except Exception as e:
                print(f"Error handling alert from {addr}: {e}")

    def register_agent(self, message, addr):
        agent_id = str(len(self.storage.get_agents()) + 1)
        self.storage.store_agent(agent_id, addr)
        print(f"Agent {agent_id} registered at {addr}")
        response = {"status": "registered", "agent_id": agent_id}
        self.udp_socket.sendto(json.dumps(response).encode(), addr)

    def process_metrics(self, message, addr):
        agent_id = message.get("agent_id")
        metrics = message.get("metrics")
        if agent_id and metrics:
            print(f"[INFO] Received metrics from {agent_id}: {metrics}")
            self.storage.store_metrics(agent_id, metrics)

            # Send ACK back to the agent
            ack_message = {"message": "metrics_ack", "agent_id": agent_id, "status": "received"}
            self.udp_socket.sendto(json.dumps(ack_message).encode(), addr)
            print(f"[DEBUG] Sent ACK for metrics to agent {agent_id}")
        else:
            print(f"[WARNING] Invalid metrics message: {message}")


    def send_task_to_agents(self, task_config):
        for device in task_config.devices:
            agent_address = self.storage.get_agent_address_by_device_id(device.device_id)
            if agent_address:
                task_data = {
                    "task_id": task_config.task_id,
                    "frequency": task_config.frequency,
                    "device_id": device.device_id,
                    "device_metrics": vars(device.device_metrics),
                    "link_metrics": vars(device.link_metrics),
                    "alertflow_conditions": vars(device.alertflow_conditions)
                }
                self.udp_socket.sendto(json.dumps(task_data).encode(), agent_address)
                print(f"Sent task to agent {device.device_id}")
            else:
                print(f"Agent {device.device_id} not found.")


if __name__ == "__main__":
    udp_port = 5005
    tcp_port = 5070
    server = NMS_Server(udp_port, tcp_port)
    server.start()
