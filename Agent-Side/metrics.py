import psutil
import subprocess

class MetricCollector:
    def __init__(self):
        pass

    def get_cpu_usage(self):
        try:
            return psutil.cpu_percent(interval=1)
        except Exception:
            return None

    def get_ram_usage(self):
        try:
            return psutil.virtual_memory().percent
        except Exception:
            return None

    def run_command(self, command):
        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            return result.stdout
        except Exception:
            return None

    def parse_iperf_output(self, output):
        try:
            lines = output.splitlines()
            for line in lines:
                if "bits/sec" in line:
                    bandwidth = line.split()[-2] + " " + line.split()[-1]
                    return {"bandwidth": bandwidth}
            return None
        except Exception:
            return None

    def parse_ping_output(self, output):
        try:
            lines = output.splitlines()
            for line in lines:
                if "rtt" in line:
                    latency_values = line.split("=")[1].split("/")[0]
                    return {"latency": float(latency_values)}
            return None
        except Exception:
            return None

    def get_bandwidth(self, tool_config):
        if not tool_config.get("enabled") or not tool_config.get("server_address"):
            return None

        if tool_config["role"] == "server":
            command = [tool_config["tool"], "-s"]
            try:
                subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return {"status": "server_running"}
            except Exception:
                return None

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
