# nms_agent.py
import time
import psutil
from NetTask_Agent import UDP_IP, UDP_PORT, send_registration_message
#from AlertFlow_Agent import TCP_IP, TCP_PORT, send_alert

def monitor_network_metrics(task_config):
    while True:
        # Monitoriza CPU e RAM
        cpu_usage = psutil.cpu_percent(interval=1)
        ram_usage = psutil.virtual_memory().percent
        print(f"CPU: {cpu_usage}% | RAM: {ram_usage}%")
        
        # Envia alertas caso os limites sejam ultrapassados
        if cpu_usage > task_config['devices'][0]['alertflow_conditions']['cpu_usage']:
            send_alert("cpu_usage", cpu_usage, task_config['devices'][0]['alertflow_conditions']['cpu_usage'])
        if ram_usage > task_config['devices'][0]['alertflow_conditions']['ram_usage']:
            send_alert("ram_usage", ram_usage, task_config['devices'][0]['alertflow_conditions']['ram_usage'])
        
        time.sleep(task_config['frequency'])

def nms_agent():
    # Regista o agente e recebe a configuração
    task_config = send_registration_message()
    
    # Inicia a monitorização das métricas
    monitor_network_metrics(task_config)

if __name__ == "__main__":
    nms_agent()






'''
def register_agent(server_ip, server_port, agent_id):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        message = f"REGISTER {agent_id}"
        sock.sendto(message.encode(), (server_ip, server_port))


# Configuração do iperf para largura de banda
def check_bandwidth(server_ip):
    result = subprocess.run(
        ["iperf3", "-c", server_ip, "-t", "10"], 
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("Largura de Banda:", result.stdout)
    else:
        print("Erro ao medir largura de banda:", result.stderr)


# Configuração do iperf para jitter e latência (UDP)
def check_jitter(server_ip):
    result = subprocess.run(
        ["iperf3", "-c", server_ip, "-u", "-t", "10"], 
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("Jitter:", result.stdout)
    else:
        print("Erro ao medir jitter:", result.stderr)

check_bandwidth("endereco_do_servidor")
check_jitter("endereco_do_servidor")

def check_latency(destination):
    result = subprocess.run(
        ["ping", "-c", "4", destination], 
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("Latência:", result.stdout)
    else:
        print("Erro ao medir latência:", result.stderr)

check_latency("endereco_do_destino")


def check_packet_loss(destination):
    result = subprocess.run(
        ["ping", "-c", "10", destination], 
        capture_output=True, text=True
    )
    if result.returncode == 0:
        # Extrair informação sobre perda de pacotes
        packet_loss_line = [line for line in result.stdout.splitlines() if "loss" in line]
        print("Perda de Pacotes:", packet_loss_line[0])
    else:
        print("Erro ao medir perda de pacotes:", result.stderr)

check_packet_loss("endereco_do_destino")


def monitor_network_metrics(server_ip):
    while True:
        cpu_usage = psutil.cpu_percent(interval=1)
        ram_usage = psutil.virtual_memory().percent
        print(f"CPU: {cpu_usage}% | RAM: {ram_usage}%")
        
        check_bandwidth(server_ip)
        check_jitter(server_ip)
        check_latency(server_ip)
        check_packet_loss(server_ip)
        
        # Espera para a próxima coleta
        time.sleep(10)  # ou a frequência definida

monitor_network_metrics("endereco_do_servidor")
'''