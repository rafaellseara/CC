import threading
import socket
import json
import logging
import curses
from NetTask_Server import NetTask
from AlertFlow_Server import AlertFlow
from parse_json import TaskConfig
from UI_Server import UIServer
from storage import Storage
from threading import Thread, Timer, Lock

class NMS_Server:
    def __init__(self, udp_port, tcp_port):
        self.host = "127.0.0.1"
        self.net_task = NetTask(self.host, udp_port)
        self.alert_flow = AlertFlow(self.host, tcp_port)
        self.storage = Storage()

        #Task Configuration
        self.task_config = None
        self.task_path = None

        # Timer and lock for task dispatch
        self.task_timer = None
        self.task_delay = 10  # seconds
        self.timer_lock = threading.Lock()

        #Threading for server functionality + UI
        self.server_thread = None
        self.ui = UIServer(self)

        #Struct to store log messages
        self.log_messages = []

        #Configure logging
        self.configure_logging()

############################################################################################################################################################################################

    def start(self):
        server_ip = socket.gethostbyname(self.host)
        logging.info(f"Starting NMS_Server on IP: {server_ip}")
        threading.Thread(target=self.alert_flow.start).start()

        try:
            #Start the server thread
            self.server_thread = Thread(target=self.run_server, daemon=True)
            self.server_thread.start()

            #Start the UI for the server
            curses.wrapper(self.ui.run_curses_ui)
        
        except Exception as e:
            logging.error(f"Error during server startup: {e}")

############################################################################################################################################################################################

    def run_server(self):
        while (self.task_path is None):
            continue

        # Ensure task_config is loaded after UI provides it
        if self.task_path:
            self.task_config = self.load_task_config(self.task_path)
            logging.info(f"Task configuration loaded: {self.task_config}")
            if not self.task_config:
                logging.error("Task configuration could not be loaded. Ensure the config file is valid.")

        # Start AlertFlow in a separate thread
        Thread(target=self.alert_flow.start, daemon=True).start()

        # Main loop for UDP (NetTask) communication
        while True:
            try:
                message, addr = self.net_task.receive_message()
                logging.info(f"Received message from {addr}: {message}")
                if message:
                    self.process_message(message, addr)
            except Exception as e:
                logging.error(f"Error processing message: {e}")

############################################################################################################################################################################################

    def stop(self):
        self.net_task.close()
        self.alert_flow.close()
        logging.info("NMS_Server stopped.")

############################################################################################################################################################################################

    def process_message(self, message, addr):
        try:
            message_type = message.get("message")
            if message_type == "register":
                self.register_agent(message, addr)
                self.schedule_task_dispatch()
            elif "metrics" in message:
                self.process_metrics(message, addr)
            elif message_type == "task_ack":
                self.process_task_ack(message)
            else:
                logging.warning(f"Unknown message type: {message}")
        except Exception as e:
            logging.error(f"Error processing message: {e}")

############################################################################################################################################################################################

    def schedule_task_dispatch(self):
        with self.timer_lock:
            if self.task_timer:
                self.task_timer.cancel()
            if self.task_config:
                self.task_timer = Timer(self.task_delay, self.send_task_to_agents)
                self.task_timer.start()

############################################################################################################################################################################################

    def register_agent(self, message, addr):
        with self.timer_lock:
            agent_id = str(len(self.net_task.registered_agents) + 1)
            self.net_task.registered_agents[agent_id] = addr
            logging.info(f"Registered agent {agent_id} at {addr}")
            ack = {"status": "registered", "agent_id": agent_id}
            self.net_task.send_message(ack, addr)

############################################################################################################################################################################################

    def send_task_to_agents(self):
        if not self.task_config:
            logging.error("Task configuration not loaded. Cannot send tasks.")
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
                logging.info(f"Sent task to agent {agent_id} at {agent_address}")
            else:
                logging.warning(f"No matching device found in task configuration for agent {agent_id}.")

############################################################################################################################################################################################

    def process_metrics(self, message, addr):
        agent_id = message.get("agent_id")
        metrics = message.get("metrics")
        if agent_id and metrics:
            logging.info(f"Received metrics from agent {agent_id}: {metrics}")

            # Store metrics using Storage
            self.storage.store_metrics_in_file(agent_id, metrics)

            # Send acknowledgment for metrics
            ack = {"message": "metrics_ack", "agent_id": agent_id}
            self.net_task.send_message(ack, addr)
            logging.info(f"Sent metrics acknowledgment to agent {agent_id}")
        else:
            logging.warning(f"Invalid metrics message: {message}")

############################################################################################################################################################################################

    def process_task_ack(self, message):
        agent_id = message.get("agent_id")
        task_id = message.get("task_id")
        if agent_id and task_id:
            logging.info(f"Received ACK for task {task_id} from agent {agent_id}.")
        else:
            logging.warning(f"Invalid task acknowledgment message: {message}")

############################################################################################################################################################################################

    def configure_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
        )

        # Add a custom handler to store logs in a list
        class ListHandler(logging.Handler):
            def __init__(self, log_storage):
                super().__init__()
                self.log_storage = log_storage

            def emit(self, record):
                log_entry = self.format(record)
                self.log_storage.append(log_entry)

        list_handler = ListHandler(self.log_messages)
        list_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
        logging.getLogger().addHandler(list_handler)

############################################################################################################################################################################################

    def get_logs(self):
        return "\n".join(self.log_messages)
    
############################################################################################################################################################################################

    def load_task_config(self, config_path):
        try:
            task_config = TaskConfig.from_json(config_path)
            if task_config:
                logging.info("Loaded TaskConfig.")
                return task_config
            else:
                logging.warning("Failed to load TaskConfig.")
        except Exception as e:
            logging.error(f"Error loading TaskConfig: {e}")
        return None
    
############################################################################################################################################################################################

if __name__ == "__main__":
    udp_port = 5005
    tcp_port = 5070
    server = NMS_Server(udp_port, tcp_port)
    try:
        server.start()
    except KeyboardInterrupt:
        logging.info("Shutting down server.")
        server.stop()
