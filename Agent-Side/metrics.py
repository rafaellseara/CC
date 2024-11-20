import psutil
import subprocess
import random
import json

class MetricCollector:
    def __init__(self):
        pass

    # Collect CPU usage
    def get_cpu_usage(self):
        return psutil.cpu_percent(interval=1)

    # Collect RAM usage
    def get_ram_usage(self):
        return psutil.virtual_memory().percent

    # Collect bandwidth using iperf
    def get_bandwidth(self, tool_config):
        if not tool_config.get("enabled"):
            return None
        
        command = [
            tool_config["tool"],
            "-c" if tool_config["role"] == "client" else "-s",
            tool_config.get("server_address", ""),
            "-t", str(tool_config.get("duration", 10)),
        ]

        if tool_config["transport_type"] == "UDP":
            command.append("-u")

        try:
            result = subprocess.run(
                [arg for arg in command if arg],  # Remove empty arguments
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return self.parse_iperf_output(result.stdout)
        except FileNotFoundError:
            print(f"Error: {tool_config['tool']} is not installed or not found in PATH.")
            return None

    def parse_iperf_output(self, output):
        # Parse iperf output for bandwidth and other stats
        try:
            lines = output.splitlines()
            for line in lines:
                if "bits/sec" in line:
                    bandwidth = line.split()[-2] + " " + line.split()[-1]
                    return {"bandwidth": bandwidth}
            return None
        except Exception as e:
            print(f"Error parsing iperf output: {e}")
            return None

    # Simulate jitter using iperf or UDP results
    def get_jitter(self, tool_config):
        if not tool_config.get("enabled"):
            return None

        command = [
            tool_config["tool"],
            "-c" if tool_config["role"] == "client" else "-s",
            tool_config.get("server_address", ""),
            "-t", str(tool_config.get("duration", 10)),
            "-u"
        ]

        try:
            result = subprocess.run(
                [arg for arg in command if arg],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return self.parse_jitter_output(result.stdout)
        except FileNotFoundError:
            print(f"Error: {tool_config['tool']} is not installed or not found in PATH.")
            return None

    def parse_jitter_output(self, output):
        # Extract jitter value from iperf output
        try:
            lines = output.splitlines()
            for line in lines:
                if "ms" in line and "jitter" in line.lower():
                    jitter = line.split()[-2]  # Assuming jitter value is in the second-to-last field
                    return {"jitter": jitter}
            return None
        except Exception as e:
            print(f"Error parsing jitter output: {e}")
            return None

    # Collect packet loss using iperf (if supported) or simulate
    def get_packet_loss(self, tool_config):
        if not tool_config.get("enabled"):
            return None

        command = [
            tool_config["tool"],
            "-c" if tool_config["role"] == "client" else "-s",
            tool_config.get("server_address", ""),
            "-t", str(tool_config.get("duration", 10)),
            "-u"
        ]

        try:
            result = subprocess.run(
                [arg for arg in command if arg],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return self.parse_packet_loss_output(result.stdout)
        except FileNotFoundError:
            print(f"Error: {tool_config['tool']} is not installed or not found in PATH.")
            return None

    def parse_packet_loss_output(self, output):
        # Extract packet loss from iperf output
        try:
            lines = output.splitlines()
            for line in lines:
                if "%" in line and "loss" in line.lower():
                    packet_loss = line.split()[-2].strip("%")  # Assuming loss percentage is in the second-to-last field
                    return {"packet_loss": float(packet_loss)}
            return None
        except Exception as e:
            print(f"Error parsing packet loss output: {e}")
            return None

    # Collect latency using ping
    def get_latency(self, ping_config):
        if not ping_config.get("enabled"):
            return None

        command = [
            "ping",
            "-c", str(ping_config.get("packet_count", 4)),
            ping_config["destination"]
        ]

        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return self.parse_ping_output(result.stdout)
        except FileNotFoundError:
            print("Error: Ping is not installed or not found in PATH.")
            return None

    def parse_ping_output(self, output):
        # Extract latency from ping output
        try:
            lines = output.splitlines()
            for line in lines:
                if "rtt" in line:
                    latency_values = line.split("=")[1].split("/")[0]
                    return {"latency": float(latency_values)}
            return None
        except Exception as e:
            print(f"Error parsing ping output: {e}")
            return None

    # Collect all metrics
    def collect_all_metrics(self, task):
        metrics = {
            "cpu_usage": self.get_cpu_usage(),
            "ram_usage": self.get_ram_usage(),
            "link_metrics": {}
        }

        link_metrics = task.get("link_metrics", {})
        for metric_name, config in link_metrics.items():
            if metric_name == "bandwidth":
                metrics["link_metrics"]["bandwidth"] = self.get_bandwidth(config)
            elif metric_name == "jitter":
                metrics["link_metrics"]["jitter"] = self.get_jitter(config)
            elif metric_name == "packet_loss":
                metrics["link_metrics"]["packet_loss"] = self.get_packet_loss(config)
            elif metric_name == "latency":
                metrics["link_metrics"]["latency"] = self.get_latency(config)

        return metrics
