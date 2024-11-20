import psutil
import subprocess
import random

class MetricCollector:
    def _init_(self):
        pass

    # Collect CPU usage
    def get_cpu_usage(self):
        return psutil.cpu_percent(interval=1)

    # Collect RAM usage
    def get_ram_usage(self):
        return psutil.virtual_memory().percent

    # Collect bandwidth usage (approximation)
    def get_bandwidth_usage(self):
        net_io = psutil.net_io_counters()
        # Return bytes sent and received as a proxy for bandwidth
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv
        }

    # Simulate jitter measurement
    def get_jitter(self):
        # Simulating jitter as a random float (real-world usage would involve tools like ping)
        return round(random.uniform(0.1, 5.0), 2)

    # Simulate packet loss
    def get_packet_loss(self):
        # Simulating packet loss as a percentage (real-world requires custom tools/scripts)
        return round(random.uniform(0, 2.0), 2)

    # Simulate latency
    def get_latency(self):
        # Example using ping to measure latency (in milliseconds)
        try:
            output = subprocess.check_output(
                ["ping", "-c", "1", "8.8.8.8"], stderr=subprocess.STDOUT, text=True
            )
            # Extract latency from the output
            for line in output.splitlines():
                if "time=" in line:
                    return float(line.split("time=")[1].split(" ")[0])
        except subprocess.CalledProcessError:
            return None  # If ping fails, return None or a default value

    # Collect all metrics
    def collect_all_metrics(self):
        metrics = {
            "cpu_usage": self.get_cpu_usage(),
            "ram_usage": self.get_ram_usage(),
            "link_metrics": {
                "bandwidth": self.get_bandwidth_usage(),
                "jitter": self.get_jitter(),
                "packet_loss": self.get_packet_loss(),
                "latency": self.get_latency()
            }
        }
        return metrics
