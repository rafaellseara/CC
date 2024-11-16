import time
import psutil
import subprocess
import socket
import json
from NetTask_Agent import UDP_IP, UDP_PORT, send_registration_message
from AlertFlow_Agent import send_alert

AGENT_ID = "agent_001"

def check_bandwidth(server_ip):
    result = subprocess.run(["iperf3", "-c", server_ip, "-t", "10"], capture_output=True, text=True)
    if result.returncode == 0:
        print("Bandwidth:", result.stdout)
    else:
        print("Error measuring bandwidth:", result.stderr)


def check_jitter(server_ip):
    result = subprocess.run(["iperf3", "-c", server_ip, "-u", "-t", "10"], capture_output=True, text=True)
    if result.returncode == 0:
        print("Jitter:", result.stdout)
    else:
        print("Error measuring jitter:", result.stderr)


def check_latency(destination, packet_count):
    result = subprocess.run(["ping", "-c", str(packet_count), destination], capture_output=True, text=True)
    if result.returncode == 0:
        print("Latency:", result.stdout)
    else:
        print("Error measuring latency:", result.stderr)


def check_packet_loss(destination):
    result = subprocess.run(["ping", "-c", "10", destination], capture_output=True, text=True)
    if result.returncode == 0:
        packet_loss_line = [line for line in result.stdout.splitlines() if "loss" in line]
        print("Packet Loss:", packet_loss_line[0])
    else:
        print("Error measuring packet loss:", result.stderr)


def monitor_network_metrics(task_config):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    while True:
        cpu_usage = psutil.cpu_percent(interval=1)
        ram_usage = psutil.virtual_memory().percent
        print(f"CPU: {cpu_usage}% | RAM: {ram_usage}%")

        # Send metrics to NMS_Server
        metrics_message = json.dumps({
            "agent_id": AGENT_ID,
            "cpu_usage": cpu_usage,
            "ram_usage": ram_usage
        })
        sock.sendto(metrics_message.encode(), (UDP_IP, UDP_PORT))

        # Check for alerts and send if necessary
        cpu_threshold = task_config['devices'][0]['alertflow_conditions']['cpu_usage']
        if cpu_usage > cpu_threshold:
            send_alert("cpu_usage", cpu_usage, cpu_threshold, AGENT_ID)

        ram_threshold = task_config['devices'][0]['alertflow_conditions']['ram_usage']
        if ram_usage > ram_threshold:
            send_alert("ram_usage", ram_usage, ram_threshold, AGENT_ID)

        time.sleep(task_config['frequency'])

def nms_agent():
    # Register the agent and get configuration
    task_config = send_registration_message(AGENT_ID)
    print("Task received and starting metric collection.")

    # Start monitoring network metrics
    monitor_network_metrics(task_config)

if __name__ == "__main__":
    nms_agent()