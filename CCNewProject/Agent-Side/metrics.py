import psutil

# Metric collection class
class MetricCollector:
    def __init__(self):
        pass

    # Collect CPU usage
    def get_cpu_usage(self):
        return psutil.cpu_percent(interval=1)

    # Collect RAM usage
    def get_ram_usage(self):
        return psutil.virtual_memory().percent

    # Collect interface stats
    def get_interface_stats(self):
        stats = {}
        for interface, addrs in psutil.net_if_addrs().items():
            stats[interface] = {
                "packets_sent": psutil.net_if_stats()[interface].bytes_sent,
                "packets_recv": psutil.net_if_stats()[interface].bytes_recv
            }
        return stats

    # Collect all metrics
    def collect_all_metrics(self):
        metrics = {
            "cpu_usage": self.get_cpu_usage(),
            "ram_usage": self.get_ram_usage(),
            "interface_stats": self.get_interface_stats()
        }
        return metrics
