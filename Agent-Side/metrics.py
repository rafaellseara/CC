import psutil
import subprocess

class MetricCollector:
    def __init__(self):
        pass

    def get_cpu_usage(self):
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            print(f"[DEBUG] Collected CPU Usage: {cpu_usage}%")
            return cpu_usage
        except Exception as e:
            print(f"[ERROR] Failed to collect CPU usage: {e}")
            return None

    def get_ram_usage(self):
        try:
            ram_usage = psutil.virtual_memory().percent
            print(f"[DEBUG] Collected RAM Usage: {ram_usage}%")
            return ram_usage
        except Exception as e:
            print(f"[ERROR] Failed to collect RAM usage: {e}")
            return None

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

    def parse_iperf_output(self, output):
        try:
            lines = output.splitlines()
            for line in lines:
                if "bits/sec" in line:
                    bandwidth = line.split()[-2] + " " + line.split()[-1]
                    print(f"[DEBUG] Parsed Bandwidth: {bandwidth}")
                    return {"bandwidth": bandwidth}
            print("[DEBUG] No Bandwidth data found in iperf output.")
            return None
        except Exception as e:
            print(f"[ERROR] Error parsing iperf output: {e}")
            return None

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

    def get_bandwidth(self, tool_config):
        if not tool_config.get("enabled") or not tool_config.get("server_address"):
            return None

        if tool_config["role"] == "server":
            if not hasattr(self, '_server_process') or self._server_process.poll() is not None:
                # Start the server process if not already running
                command = [tool_config["tool"], "-s"]
                print("[DEBUG] Starting iperf in server mode.")
                self._server_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                print("[DEBUG] Iperf server started successfully.")
            return {"status": "server_running"}
        elif tool_config["role"] == "client":
            command = [
                tool_config["tool"],
                "-c", tool_config["server_address"],
                "-t", str(tool_config.get("duration", 10)),
            ]
            if tool_config["transport_type"] == "UDP":
                command.append("-u")

            output = self.run_command(command)
            if output:
                return self.parse_iperf_output(output)
        return None

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

        print(f"[DEBUG] Collected Metrics: {metrics}")
        return metrics
