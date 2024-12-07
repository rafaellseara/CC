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
        self.host = self.local_ip()

        # Initialize the logger early
        self.log_messages = []
        self.configure_logging()

        # Pass the root logger to dependencies
        self.net_task = NetTask(self.host, udp_port, logging.getLogger())
        self.alert_flow = AlertFlow(self.host, tcp_port, logging.getLogger())
        self.storage = Storage(logging.getLogger())

        self.task_config = None
        self.task_path = None

        # Timer and lock for task dispatch
        self.task_timer = None
        self.task_delay = 10
        self.timer_lock = threading.Lock()

        self.server_thread = None
        self.ui = UIServer(self)

############################################################################################################################################################################################
    
    def local_ip(self):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            try:
                s.connect(("1.1.1.1", 53))
                local_ip_address = s.getsockname()[0]
            except Exception as e:
                logging.error(f"Could not determine local IP: {e}")
                local_ip_address = None
            return local_ip_address

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
            logging.error(f"Failed to start server: {e}")

############################################################################################################################################################################################

    def run_server(self):
        while (self.task_path is None):
            continue

        # Ensure task_config is loaded after UI provides it
        if self.task_path:
            self.task_config = self.load_task_config(self.task_path)
            logging.info(f"Task configuration loaded")
            if not self.task_config:
                logging.error("Failed to load Task configuration")

        # Start AlertFlow in a separate thread
        #Thread(target=self.alert_flow.start, daemon=True).start()

        # Main loop for UDP (NetTask) communication
        while True:
            try:
                message, addr = self.net_task.receive_message()
                logging.info(f"Received message from {addr}: {message}")
                if message:
                    self.process_message(message, addr)
            except Exception as e:
                logging.error(f"Failed to process message: {e}")

############################################################################################################################################################################################

    def stop(self):
        self.net_task.close()
        self.alert_flow.close()
        logging.info("NMS_Server stopped")

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
            logging.error(f"Failed to process message: {e}")

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
            logging.info(f"Agent {agent_id} registered with address {addr}")
            ack = {"status": "registered", "agent_id": agent_id}
            self.net_task.send_message(ack, addr)

############################################################################################################################################################################################

    def send_task_to_agents(self, max_retries=3, wait_time=5):
        """
        Sends tasks to registered agents in parallel threads.
        Each thread waits for acknowledgment (ACK) and handles retransmissions.
        """
        if not self.task_config:
            logging.error("Failed to load Task configuration. Cannot send tasks.")
            return

        # Create the dedicated ACK socket
        ack_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        ack_port = self.net_task.udp_port + 1  # Use a port offset for ACK
        ack_socket.bind((self.net_task.host, ack_port))
        ack_socket.settimeout(wait_time)
        logging.info(f"ACK socket created and listening on port {ack_port}")

        def send_task_to_agent(agent_id, agent_address, task_data):
            retries = 0
            ack_received = False

            while retries < max_retries and not ack_received:
                # Send the task to the agent´
                ack_socket.sendto(json.dumps(task_data).encode(),agent_address)
                #self.net_task.send_message(task_data, agent_address, agent_id=agent_id)
                logging.info(f"Sent task to agent {agent_id} with address {agent_address} (Attempt {retries + 1})")

                try:
                    # Wait for a response for a fixed amount of time
                    data, addr = ack_socket.recvfrom(1024)
                    message = json.loads(data.decode())

                    # Check if the message is an ACK
                    if message.get("message") == "task_ack" and message.get("task_id") == task_data["task_id"]:
                        logging.info(f"Received ACK for task {task_data['task_id']} from agent {agent_id}.")
                        ack_received = True
                        break
                    else:
                        logging.warning(f"Received unexpected message: {message} from agent {agent_id}. Retrying...")
                except socket.timeout:
                    logging.warning(f"No ACK received from agent {agent_id} for task {task_data['task_id']}. Retrying...")
                    retries += 1
                except Exception as e:
                    logging.error(f"Error while waiting for ACK: {e}")
                    retries += 1

            if not ack_received:
                logging.error(f"Failed to receive ACK from agent {agent_id} after {max_retries} retries.")

        # Prepare task data for each agent
        threads = []
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
                    "alertflow_conditions": vars(device.alertflow_conditions),
                }
                # Start a thread to handle task transmission for each agent
                thread = threading.Thread(target=send_task_to_agent, args=(agent_id, agent_address, task_data), daemon=True)
                thread.start()
                threads.append(thread)
            else:
                logging.warning(f"No matching device found in task configuration for agent {agent_id}.")

        # Wait for all threads to finish
        for thread in threads:
            thread.join()

        # Close the ACK socket after all tasks are processed
        ack_socket.close()
        logging.info("ACK socket closed.")

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
            logging.info(f"Sent metrics ACK to agent {agent_id}")
        else:
            logging.warning(f"Invalid metrics message: {message}")

############################################################################################################################################################################################

    def process_task_ack(self, message):
        agent_id = message.get("agent_id")
        task_id = message.get("task_id")
        if agent_id and task_id:
            logging.info(f"Received ACK for task {task_id} from agent {agent_id}.")
        else:
            logging.warning(f"Invalid task ACK message: {message}")

############################################################################################################################################################################################

    def configure_logging(self):
        # Remove all existing handlers to prevent duplicate outputs
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # Add a custom handler to store logs in the log_messages list
        class ListHandler(logging.Handler):
            def __init__(self, log_storage):
                super().__init__()
                self.log_storage = log_storage

            def emit(self, record):
                log_entry = self.format(record)
                self.log_storage.append(log_entry)

        list_handler = ListHandler(self.log_messages)
        list_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

        # Attach the ListHandler to the root logger
        logging.getLogger().addHandler(list_handler)

        # Ensure the root logger uses only the ListHandler
        logging.getLogger().setLevel(logging.INFO)
        
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
                logging.warning("Failed to load TaskConfig")
        except Exception as e:
            logging.error(f"Failed to load TaskConfig: {e}")
        return None
    
############################################################################################################################################################################################

if __name__ == "__main__":
    udp_port = 5005
    tcp_port = 5070
    server = NMS_Server(udp_port, tcp_port)
    try:
        server.start()
    except KeyboardInterrupt:
        logging.info("Shutting down server...")
        server.stop()
