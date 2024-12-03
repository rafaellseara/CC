import threading
import socket
import json
from NetTask_Server import NetTask
from AlertFlow_Server import AlertFlow
from parse_json import TaskConfig
from storage import Storage

class NMS_Server:
    def __init__(self, udp_port, tcp_port):
        self.host = "127.0.0.1"
        self.net_task = NetTask(self.host, udp_port)
        self.alert_flow = AlertFlow(self.host, tcp_port)
        self.storage = Storage()

        # Timer and lock for task dispatch
        self.task_timer = None
        self.task_delay = 10  # seconds
        self.timer_lock = threading.Lock()

        # Load the task configuration at server startup
        self.task_config = self.load_task_config("task_config.json")
        if not self.task_config:
            print("[ERROR] Task configuration could not be loaded. Ensure 'task_config.json' is valid.")

############################################################################################################################################################################################

    def start(self):
        server_ip = socket.gethostbyname(self.host)
        print(f"[INFO] Starting NMS_Server on IP: {server_ip}")
        threading.Thread(target=self.alert_flow.start).start()

        # Main loop for UDP (NetTask) communication
        while True:
            message, addr = self.net_task.receive_message()
            if message:
                self.process_message(message, addr)

############################################################################################################################################################################################

    def stop(self):
        self.net_task.close()
        self.alert_flow.close()
        print("[INFO] NMS_Server stopped.")

############################################################################################################################################################################################

    def process_message(self, message, addr):
        """
        Processes incoming UDP messages based on their type.
        """
        if message.get("message") == "register":
            self.register_agent(message, addr)

            # Use a timer to delay task dispatch
            with self.timer_lock:
                if self.task_timer:
                    self.task_timer.cancel()
                if self.task_config:
                    self.task_timer = threading.Timer(self.task_delay, self.send_task_to_agents)
                    self.task_timer.start()
        elif "metrics" in message:
            self.process_metrics(message, addr)
        elif message.get("message") == "task_ack":
            self.process_task_ack(message)
        else:
            print(f"[WARNING] Unknown message type: {message}")

############################################################################################################################################################################################

    def register_agent(self, message, addr):
        """
        Registers an agent and sends an acknowledgment.
        """
        # Assign a unique agent ID
        agent_id = str(len(self.net_task.registered_agents) + 1)

        # Store the agent's address
        self.net_task.registered_agents[agent_id] = addr

        print(f"[INFO] Registered agent {agent_id} at {addr}")

        # Send acknowledgment back to the agent
        ack = {"status": "registered", "agent_id": agent_id}
        self.net_task.send_message(ack, addr)

############################################################################################################################################################################################

    def send_task_to_agents(self):
        """
        Sends tasks to all registered agents based on the task configuration.
        """
        if not self.task_config:
            print("[ERROR] Task configuration not loaded. Cannot send tasks.")
            return

        for agent_id, agent_address in self.net_task.registered_agents.items():
            # Find the matching device in the task configuration
            device = next((d for d in self.task_config.devices if d.device_id == agent_id), None)
            if device:
                task_data = {
                    "task_id": self.task_config.task_id,
                    "frequency": self.task_config.frequency,
                    "device_id": device.device_id,
                    "device_metrics": vars(device.device_metrics),
                    "link_metrics": vars(device.link_metrics),
                    "alertflow_conditions": vars(device.alertflow_conditions)
                }
                self.net_task.send_message(task_data, agent_address, agent_id=agent_id)
                print(f"[INFO] Sent task to agent {agent_id} at {agent_address}")
            else:
                print(f"[WARNING] No matching device found in task configuration for agent {agent_id}.")

############################################################################################################################################################################################

    def process_metrics(self, message, addr):
        """
        Processes metrics received from agents and sends acknowledgment.
        Also stores the metrics in a JSON file for each agent.
        """
        agent_id = message.get("agent_id")
        metrics = message.get("metrics")
        if agent_id and metrics:
            print(f"[INFO] Received metrics from agent {agent_id}: {metrics}")

            # Store metrics using Storage
            self.storage.store_metrics_in_file(agent_id, metrics)

            # Send acknowledgment for metrics
            ack = {"message": "metrics_ack", "agent_id": agent_id}
            self.net_task.send_message(ack, addr)
            print(f"[INFO] Sent metrics acknowledgment to agent {agent_id}")
        else:
            print(f"[WARNING] Invalid metrics message: {message}")

############################################################################################################################################################################################

    def process_task_ack(self, message):
        """
        Processes task acknowledgments from agents.
        """
        agent_id = message.get("agent_id")
        task_id = message.get("task_id")
        if agent_id and task_id:
            print(f"[INFO] Received ACK for task {task_id} from agent {agent_id}.")
        else:
            print(f"[WARNING] Invalid task acknowledgment message: {message}")

############################################################################################################################################################################################


    def load_task_config(self, config_path):
        """
        Loads the task configuration from a JSON file.
        """
        try:
            task_config = TaskConfig.from_json(config_path)
            if task_config:
                print("[INFO] Loaded TaskConfig.")
                return task_config
            else:
                print("[WARNING] Failed to load TaskConfig.")
        except Exception as e:
            print(f"[ERROR] Error loading TaskConfig: {e}")
        return None


if __name__ == "__main__":
    udp_port = 5005
    tcp_port = 5070
    server = NMS_Server(udp_port, tcp_port)
    try:
        server.start()
    except KeyboardInterrupt:
        print("[INFO] Shutting down server.")
        server.stop()
