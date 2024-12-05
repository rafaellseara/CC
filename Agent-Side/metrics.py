import psutil
import subprocess
import select
import time
from time import sleep

class MetricCollector:
    def __init__(self):
        self.prev_net_stats = {}

############################################################################################################################################################################################

    def get_cpu_usage(self):
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            print(f"[DEBUG] Collected CPU Usage: {cpu_usage}%")
            return cpu_usage
        except Exception as e:
            print(f"[ERROR] Failed to collect CPU usage: {e}")
            return None

############################################################################################################################################################################################

    def get_ram_usage(self):
        try:
            ram_usage = psutil.virtual_memory().percent
            print(f"[DEBUG] Collected RAM Usage: {ram_usage}%")
            return ram_usage
        except Exception as e:
            print(f"[ERROR] Failed to collect RAM usage: {e}")
            return None

############################################################################################################################################################################################

    def get_interface_stats(self, interfaces):
        try:
            current_stats = psutil.net_io_counters(pernic=True)
            interface_stats = {}

            for iface in interfaces:
                if iface in current_stats:
                    if iface in self.prev_net_stats:
                        prev = self.prev_net_stats[iface]
                        curr = current_stats[iface]
                        interface_stats[iface] = {
                            "bytes_sent": curr.bytes_sent - prev.bytes_sent,
                            "bytes_recv": curr.bytes_recv - prev.bytes_recv,
                            "packets_sent": curr.packets_sent - prev.packets_sent,
                            "packets_recv": curr.packets_recv - prev.packets_recv,
                            "dropin": curr.dropin - prev.dropin,
                            "dropout": curr.dropout - prev.dropout,
                        }
                    else:
                        # No previous stats; provide current as initial stats
                        stats = current_stats[iface]
                        interface_stats[iface] = {
                            "bytes_sent": stats.bytes_sent,
                            "bytes_recv": stats.bytes_recv,
                            "packets_sent": stats.packets_sent,
                            "packets_recv": stats.packets_recv,
                            "dropin": stats.dropin,
                            "dropout": stats.dropout,
                        }

            # Update previous stats for the next interval
            self.prev_net_stats = current_stats
            return interface_stats
        except Exception as e:
            print(f"[ERROR] Failed to collect interface stats: {e}")
            return {}

############################################################################################################################################################################################

    def run_command(self, command):
        try:
            print(f"[DEBUG] Running command: {' '.join(command)}")
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            print(f"[DEBUG] Command Output: {result.stdout}")
            print(f"[DEBUG] Command Error Output: {result.stderr}")
            return result.stdout
        except FileNotFoundError:
            print(f"[ERROR] Command not found: {command[0]}")
        except Exception as e:
            print(f"[ERROR] Error running command {command}: {e}")
        return None

############################################################################################################################################################################################

    def parse_iperf_output(self, output):
        try:
            lines = output.splitlines()
            parsed_data = {"bandwidth": None, "jitter": None, "packet_loss": None}

            for line in lines:
                # Parse bandwidth
                if any(unit in line for unit in ["bits/sec", "Mbits/sec", "Gbits/sec"]):
                    parts = line.split()
                    # Look for bandwidth value dynamically
                    for idx, part in enumerate(parts):
                        if part in ["bits/sec", "Mbits/sec", "Gbits/sec"]:
                            bandwidth_value = parts[idx - 1]  # Value before the unit
                            parsed_data["bandwidth"] = bandwidth_value + " " + part
                            print(f"[DEBUG] Parsed Bandwidth: {parsed_data['bandwidth']}")
                            break

                # Parse jitter and packet loss for UDP transport
                if "ms" in line and "/" in line:
                    parts = line.split()
                    # Ensure there are enough parts to parse the line correctly
                    if len(parts) >= 8:
                        parsed_data["jitter"] = parts[-5] + " " + parts[-4]  # Jitter (e.g., "0.007 ms")
                        parsed_data["packet_loss"] = parts[-3] + " " + parts[-2] + " " + parts[-1]  # Packet loss (e.g., "0/895 (0%)")
                        print(f"[DEBUG] Parsed Jitter: {parsed_data['jitter']}, Packet Loss: {parsed_data['packet_loss']}")

            if any(value for value in parsed_data.values()):
                return parsed_data

            print("[DEBUG] No relevant data found in iperf output.")
            return None
        except Exception as e:
            print(f"[ERROR] Error parsing iperf output: {e}")
            return None

############################################################################################################################################################################################

    def parse_ping_output(self, output):
        try:
            lines = output.splitlines()
            for line in lines:
                if "rtt" in line:
                    latency_values = line.split("=")[1].split("/")[0]
                    print(f"[DEBUG] Parsed Latency: {latency_values} ms")
                    return {"latency": float(latency_values)}
            print("[DEBUG] No Latency data found in ping output.")
            return None
        except Exception as e:
            print(f"[ERROR] Error parsing ping output: {e}")
            return None

############################################################################################################################################################################################

    def get_bandwidth(self, tool_config):
        if not tool_config.get("enabled") or not tool_config.get("server_address"):
            print("[DEBUG] Bandwidth collection disabled or missing server address.")
            return None

        if tool_config["role"] == "server":
            if not hasattr(self, '_server_process') or self._server_process.poll() is not None:
                # Start the server process if not already running
                command = [tool_config["tool"], "-s", "-P", "1"]
                if tool_config["transport_type"] == "UDP":
                    command.append("-u")
                print(f"[DEBUG] Starting iperf in server mode with command: {' '.join(command)}")
                try:
                    self._server_process = subprocess.Popen(
                        command,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    print("[DEBUG] Iperf server started successfully.")
                except Exception as e:
                    print(f"[ERROR] Failed to start iperf server: {e}")
                    return {"status": "failed_to_start"}

            # Wait for a client to connect and generate a report with a timeout
            print("[DEBUG] Waiting for client connection to generate metrics...")
            start_time = time.time()
            timeout = 15  # Timeout in seconds
            output = ""

            try:
                while True:
                    elapsed_time = time.time() - start_time
                    if elapsed_time > timeout:
                        print("[DEBUG] Timeout reached. No client connection detected.")
                        return {"status": "server_running"}

                    # Use select to wait for output with a timeout
                    readable, _, _ = select.select([self._server_process.stdout], [], [], 1)
                    if readable:
                        line = self._server_process.stdout.readline()
                        if line:
                            output += line
                            if "Server Report" in line or "bits/sec" in line:
                                print("[DEBUG] Detected server report or bandwidth line.")
                                break

                if output:
                    print("[DEBUG] Captured iperf server output. Parsing...")
                    return self.parse_iperf_output(output)

                print("[DEBUG] No output captured from iperf server.")
                return {"status": "server_running"}
            except Exception as e:
                print(f"[ERROR] Error capturing iperf server metrics: {e}")
                return {"status": "error_capturing_metrics"}

        elif tool_config["role"] == "client":
            command = [
                tool_config["tool"],
                "-c", tool_config["server_address"],
                "-t", str(tool_config.get("duration", 10)),
            ]
            if tool_config["transport_type"] == "UDP":
                command.append("-u")

            print(f"[DEBUG] Starting iperf client with command: {' '.join(command)}")
            output = self.run_command(command)
            if output:
                print("[DEBUG] Captured iperf client output. Parsing...")
                return self.parse_iperf_output(output)
            else:
                print("[DEBUG] No output captured from iperf client.")
        return None

############################################################################################################################################################################################

    def get_latency(self, ping_config):
        if not ping_config.get("enabled") or not ping_config.get("destination"):
            print("[DEBUG] Latency metric skipped: Missing or disabled configuration.")
            return None

        command = [
            "ping",
            "-c", str(ping_config.get("packet_count", 4)),
            ping_config["destination"]
        ]

        output = self.run_command(command)
        if output:
            return self.parse_ping_output(output)
        return None

############################################################################################################################################################################################

    def collect_all_metrics(self, task):
        print("[DEBUG] Starting metrics collection for task:", task.get("task_id"))
        metrics = {
            "cpu_usage": self.get_cpu_usage(),
            "ram_usage": self.get_ram_usage(),
            "link_metrics": {}
        }

        link_metrics = task.get("link_metrics", {})
        for metric_name, config in link_metrics.items():
            if metric_name == "bandwidth":
                metrics["link_metrics"]["bandwidth"] = self.get_bandwidth(config)
            elif metric_name == "latency":
                metrics["link_metrics"]["latency"] = self.get_latency(config)
                
        return metrics
    
############################################################################################################################################################################################

    def collect_all_metrics(self, task):
        print("[DEBUG] Starting metrics collection for task:", task.get("task_id"))
        metrics = {
            "cpu_usage": self.get_cpu_usage(),
            "ram_usage": self.get_ram_usage(),
            "interface_stats": {},
            "link_metrics": {}
        }

        # Collect interface stats if specified in task
        device_metrics = task.get("device_metrics", {})
        interfaces = device_metrics.get("interface_stats", [])
        if interfaces:
            metrics["interface_stats"] = self.get_interface_stats(interfaces)

        # Collect link metrics
        link_metrics = task.get("link_metrics", {})
        for metric_name, config in link_metrics.items():
            if metric_name == "bandwidth":
                metrics["link_metrics"]["bandwidth"] = self.get_bandwidth(config)
            elif metric_name == "latency":
                metrics["link_metrics"]["latency"] = self.get_latency(config)
                
        return metrics

