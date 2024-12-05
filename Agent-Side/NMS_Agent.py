import socket
import json
import time
import threading
import logging
import sys
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
                    print(f"Agent {self.agent_id} successfully registered")
                    return True  # Registo concluído com sucesso
                else:
                    print(f"[ERROR] Attempt {attempt}: Unexpected response: {response}")
                    return False

            except socket.timeout:
                print(f"[ERROR] Attempt {attempt}: No response from server, retrying...")

            except Exception as e:
                print(f"[ERROR] Attempt {attempt}: Error during registration: {e}")

        # Após atingir o limite de tentativas
        print("[ERROR] Failed to register agent after maximum retries.")
        return False
    
############################################################################################################################################################################################

    def receive_task(self):
        print(f"Listening for tasks from {self.server_address}")
        while True:
            try:
                # Configura o timeout no socket para evitar bloqueio indefinido
                self.udp_socket.settimeout(15)  # Ajuste o valor do timeout conforme necessário
                
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
                print("No task received within timeout period, continuing to listen...")

            except json.JSONDecodeError:
                # Tratamento para mensagens malformadas
                print("[ERROR] Received malformed task. Ignoring and continuing to listen.")

            except Exception as e:
                # Tratamento de quaisquer outras exceções
                print(f"[ERROR] Error in receive_task: {e}")


############################################################################################################################################################################################

    def send_task_ack(self, task_id):
        if not task_id:
            print("[ERROR] No task ID found to send ACK.")
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
                print(f"Collecting metrics for task ID: {task.get('task_id')}")

                # Collect all metrics, including CPU and RAM usage
                metrics = self.metric_collector.collect_all_metrics(task)
                print(f"Metrics collected: {metrics}")

                # Send metrics to the server
                self.send_metrics(metrics)

                # Check for alert conditions
                self.check_alerts(metrics, task)

                # Sleep for the frequency defined in the task
                sleep_duration = task.get("frequency", 30)
                print(f"Sleeping for {sleep_duration} seconds before next collection.")
                time.sleep(sleep_duration)
            except Exception as e:
                print(f"[ERROR] Error in collect_metrics: {e}")

############################################################################################################################################################################################

    def send_metrics(self, metrics, max_retries=3):
        retries = 0
        while retries < max_retries:
            try:
                metrics_message = {
                    "agent_id": self.agent_id,
                    "metrics": metrics
                }
                self.udp_socket.sendto(json.dumps(metrics_message).encode(), (self.server_address, self.udp_port))
                print(f"Metrics sent successfully (attempt {retries + 1}): {metrics_message}")

                # Wait for ACK from server
                if self.wait_for_ack_udp():
                    print(f"Metrics ACK received successfully from server.")
                    return  # Exit the function if ACK is received
                else:
                    print(f"[ERROR] Metrics ACK not received from server (attempt {retries + 1}). Retrying...")
            except Exception as e:
                print(f"[ERROR] Failed to send metrics (attempt {retries + 1}): {e}")

            # Increment the retry counter
            retries += 1

        # If maximum retries are reached
        print(f"[ERROR] Failed to send metrics after {max_retries} attempts. Giving up.")



############################################################################################################################################################################################

    def wait_for_ack_udp(self, max_retries=3):
        retries = 0
        while retries < max_retries:
            try:
                # Configura timeout para aguardar o ACK
                self.udp_socket.settimeout(15)  
                ack_data, _ = self.udp_socket.recvfrom(1024)
                
                # Decodifica a mensagem recebida
                ack_message = json.loads(ack_data.decode())
                
                # Verifica se o ACK é válido
                if ack_message.get("message") == "metrics_ack" and ack_message.get("agent_id") == self.agent_id:
                    logging.info(f"Received valid ACK: {ack_message}")
                    return True
                else:
                    logging.warning(f"Unexpected ACK content: {ack_message}")
            except socket.timeout:
                # Timeout ao aguardar ACK, incrementa tentativa
                retries += 1
                logging.error(f"No ACK received. Retry {retries}/{max_retries}")
            except json.JSONDecodeError:
                # Caso a mensagem seja malformada
                logging.error("Received malformed ACK. Failed to parse JSON.")
                return False
            finally:
                # Restaura timeout para estado padrão
                self.udp_socket.settimeout(None)
        
        # Se todas as tentativas falharem
        logging.error("Failed to receive ACK after maximum retries.")
        return False

############################################################################################################################################################################################

    def send_alert(self, alert_message, max_retries=3):
        """
        Sends an alert message to the server, with retransmission and ACK handling.
        
        Args:
            alert_message (str): The alert message to send.
            max_retries (int): Maximum number of retransmission attempts if no ACK is received.
        """
        retries = 0
        while retries < max_retries:
            try:
                # Cria o socket TCP
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
                    # Conecta ao servidor
                    tcp_socket.connect((self.server_address, self.tcp_port))
                    print(f"Connected to server at {self.server_address}:{self.tcp_port}")

                    # Prepara o alerta como um dicionário e converte para JSON
                    alert_data = {"alert": alert_message}
                    tcp_socket.sendall(json.dumps(alert_data).encode())
                    print(f"Sent alert to server: {alert_message}")

                    # Espera pelo ACK do servidor
                    if self.wait_for_ack_tcp():
                        print(f"Alert ACK received successfully from server.")
                        return  # Se o ACK for recebido, sai da função
                    else:
                        print(f"[ERROR] Alert ACK not received from server (attempt {retries + 1}). Retrying...")

            except Exception as e:
                print(f"[ERROR] Failed to send alert (attempt {retries + 1}): {e}")
            
            retries += 1  # Incrementa o contador de tentativas

        # Se o número máximo de tentativas for atingido
        print(f"[ERROR] Failed to send alert after {max_retries} attempts. Giving up.")



############################################################################################################################################################################################

    def wait_for_ack_tcp(self, max_retries=3):
        retries = 0
        while retries < max_retries:
            try:
                # Configura o timeout de 5 segundos para aguardar o ACK
                self.tcp_socket.settimeout(15)  
                
                # Aguarda até 5 segundos por dados
                ack_data = self.tcp_socket.recv(1024)

                # Se não receber dados após 5 segundos, tentamos novamente
                if not ack_data:
                    logging.error(f"No data received. Retry {retries + 1}/{max_retries}")
                    retries += 1
                    continue

                # Decodifica a mensagem recebida
                ack_message = json.loads(ack_data.decode())

                # Verifica se o ACK é válido
                if ack_message.get("status") == "ack" and ack_message.get("alert_received"):
                    logging.info(f"Received valid ACK: {ack_message}")
                    return True
                else:
                    logging.warning(f"Unexpected ACK content: {ack_message}")
                    retries += 1

            except json.JSONDecodeError:
                # Caso a mensagem seja malformada
                logging.error("Received malformed ACK. Failed to parse JSON.")
                retries += 1
            except socket.timeout:
                # Timeout específico, não incrementa retries até a próxima tentativa
                logging.error(f"No ACK received after waiting for 5 seconds. Retry {retries + 1}/{max_retries}")
                retries += 1
            except socket.error as e:
                # Se ocorrer erro no socket (desconexão, etc.)
                logging.error(f"Socket error: {e}. Retry {retries + 1}/{max_retries}")
                retries += 1

        # Se todas as tentativas falharem
        logging.error("Failed to receive ACK after maximum retries.")
        return False


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

        # Check Interface Stats
        interface_name = "eth0"

        # Verifica se a interface está nas métricas coletadas
        if interface_name in metrics["interface_stats"]:
            packets_recv = metrics["interface_stats"][interface_name]["packets_recv"]
            threshold = alert_conditions.get("packets_recv", float('inf'))

            # Compara o valor com o limite definido
            if packets_recv > threshold:
                alert_message = json.dumps({
                    "alert": "packets_recv",
                    "value": packets_recv,
                    "agent_id": self.agent_id,
                    "threshold": threshold,
                    "interface": interface_name
                })
                self.send_alert(alert_message)

        # Check Packet Loss
        if "packet_loss" in metrics:
            try:
                # Extraindo a percentagem de packet loss (remove parênteses e símbolo de '%')
                packet_loss_percentage = float(metrics["packet_loss"].strip("()%"))
                threshold = alert_conditions.get("packet_loss", float('inf'))

                # Comparar com o limite definido
                if packet_loss_percentage > threshold:
                    alert_message = json.dumps({
                        "alert": "packet_loss",
                        "value": packet_loss_percentage,
                        "agent_id": self.agent_id,
                        "threshold": threshold
                    })
                    self.send_alert(alert_message)
            except ValueError as e:
                print(f"[ERROR] Failed to parse packet loss value: {metrics['packet_loss']}. Error: {e}")



        # Check Jitter
        if "jitter" in metrics:
            try:
                # Extrair o valor de jitter e remover a unidade "ms"
                jitter_value = float(metrics["jitter"].split()[0])  # Pega apenas o número antes de "ms"
                threshold = alert_conditions.get("jitter", float('inf'))

                # Comparar com o limite definido
                if jitter_value > threshold:
                    alert_message = json.dumps({
                        "alert": "jitter",
                        "value": jitter_value,
                        "agent_id": self.agent_id,
                        "threshold": threshold
                    })
                    self.send_alert(alert_message)
            except (ValueError, IndexError) as e:
                print(f"[ERROR] Failed to parse jitter value: {metrics['jitter']}. Error: {e}")

############################################################################################################################################################################################

    def start(self):
        if not self.register():
            logging.error("Agent registration failed. Terminating program.")
            sys.exit(1)  # Código de saída 1 indica erro

        # Start a separate thread for receiving tasks from the server
        task_thread = threading.Thread(target=self.receive_task)
        task_thread.start()

if __name__ == "__main__":
    server_address = "10.0.0.10"
    udp_port = 5005
    tcp_port = 5070
    agent = NMS_Agent(server_address, udp_port, tcp_port)
    agent.start()