import socket
import json
import time
import threading
import logging
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

############################################################################################################################################################################################

    def register(self, max_retries=3, timeout=5):
        register_message = {
            "message": "register",
        }
        
        for attempt in range(1, max_retries + 1):
            try:
                # Envia o pedido de registo
                self.udp_socket.sendto(json.dumps(register_message).encode(), (self.server_address, self.udp_port))
                print(f"Attempt {attempt}: Sent registration request to server at {self.server_address}")

                # Configura o timeout para esperar pela resposta
                self.udp_socket.settimeout(timeout)

                # Aguarda a resposta do servidor
                data, server = self.udp_socket.recvfrom(1024)
                response = json.loads(data.decode())

                # Verifica se o registo foi bem-sucedido
                if response.get("status") == "registered":
                    self.agent_id = response.get("agent_id")
                    print(f"Agent successfully registered with assigned agent_id: {self.agent_id}")
                    return True  # Registo concluído com sucesso
                else:
                    print(f"Attempt {attempt}: Unexpected response: {response}")
                    return False

            except socket.timeout:
                print(f"Attempt {attempt}: No response from server, retrying...")

            except Exception as e:
                print(f"Attempt {attempt}: Error during registration: {e}")

        # Após atingir o limite de tentativas
        print("Failed to register agent after maximum retries.")
        return False
    
############################################################################################################################################################################################

    def receive_task(self):
        print(f"Listening for tasks from {self.server_address}")
        while True:
            try:
                # Configura o timeout no socket para evitar bloqueio indefinido
                self.udp_socket.settimeout(10)  # Ajuste o valor do timeout conforme necessário
                
                # Aguarda mensagens do servidor
                data, server = self.udp_socket.recvfrom(1024)
                task = json.loads(data.decode())
                print(f"Received task: {task}")

                # Envia um ACK para o servidor
                self.send_task_ack(task.get("task_id"))

                # Inicia a coleta de métricas com base na tarefa
                self.collect_metrics(task)

            except socket.timeout:
                # Timeout enquanto aguardava por mensagens, continua ouvindo
                print("[DEBUG] No task received within timeout period, continuing to listen...")

            except json.JSONDecodeError:
                # Tratamento para mensagens malformadas
                print("[ERROR] Received malformed task. Ignoring and continuing to listen.")

            except Exception as e:
                # Tratamento de quaisquer outras exceções
                print(f"[ERROR] Error in receive_task: {e}")


############################################################################################################################################################################################

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

############################################################################################################################################################################################

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

############################################################################################################################################################################################

    def send_metrics(self, metrics):
        try:
            metrics_message = {
                "agent_id": self.agent_id,
                "metrics": metrics
            }
            self.udp_socket.sendto(json.dumps(metrics_message).encode(), (self.server_address, self.udp_port))
            print(f"[DEBUG] Metrics sent successfully: {metrics_message}")

            # Wait for ACK from server
            if self.wait_for_ack():
                print(f"[INFO] Metrics ACK received successfully from server.")
            else:
                print(f"[WARNING] Metrics ACK not received from server.")
        except Exception as e:
            print(f"[ERROR] Failed to send metrics: {e}")


############################################################################################################################################################################################

    def wait_for_ack(self, max_retries=3):
        retries = 0
        while retries < max_retries:
            try:
                # Configura timeout para aguardar o ACK
                self.udp_socket.settimeout(5)  
                ack_data, _ = self.udp_socket.recvfrom(1024)
                
                # Decodifica a mensagem recebida
                ack_message = json.loads(ack_data.decode())
                
                # Verifica se o ACK é válido
                if ack_message.get("message") == "metrics_ack" and ack_message.get("agent_id") == self.agent_id:
                    logging.info(f"[DEBUG] Received valid ACK: {ack_message}")
                    return True
                else:
                    logging.warning(f"[WARNING] Unexpected ACK content: {ack_message}")
            except socket.timeout:
                # Timeout ao aguardar ACK, incrementa tentativa
                retries += 1
                logging.error(f"[ERROR] No ACK received. Retry {retries}/{max_retries}")
            except json.JSONDecodeError:
                # Caso a mensagem seja malformada
                logging.error("[ERROR] Received malformed ACK. Failed to parse JSON.")
                return False
            finally:
                # Restaura timeout para estado padrão
                self.udp_socket.settimeout(None)
        
        # Se todas as tentativas falharem
        logging.error("[ERROR] Failed to receive ACK after maximum retries.")
        return False

############################################################################################################################################################################################

    def send_alert(self, alert_message):
        try:
            # Cria um novo socket para enviar o alerta
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
                # Certifique-se de que o endereço do servidor está formatado corretamente como uma tupla
                server_address = (self.server_address, self.tcp_port)
                
                # Conecta ao servidor
                tcp_socket.connect(server_address)
                
                # Envia a mensagem de alerta
                tcp_socket.sendall(alert_message.encode())
                print(f"Sent alert to server: {alert_message}")
        except Exception as e:
            print(f"Failed to send alert: {e}")

############################################################################################################################################################################################

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

############################################################################################################################################################################################

    def start(self):
        self.register()

        # Start a separate thread for receiving tasks from the server
        task_thread = threading.Thread(target=self.receive_task)
        task_thread.start()

if __name__ == "__main__":
    server_address = "127.0.0.1" 
    udp_port = 5005
    tcp_port = 5070
    agent = NMS_Agent(server_address, udp_port, tcp_port)
    agent.start()