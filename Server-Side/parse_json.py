import json

class DeviceMetrics:
    def __init__(self, cpu_usage, ram_usage, interface_stats):
        self.cpu_usage = cpu_usage
        self.ram_usage = ram_usage
        self.interface_stats = interface_stats

    def __repr__(self):
        return (f"DeviceMetrics(cpu_usage={self.cpu_usage}, "
                f"ram_usage={self.ram_usage}, interface_stats={self.interface_stats})")


class LinkMetrics:
    def __init__(self, bandwidth, jitter, packet_loss, latency):
        self.bandwidth = bandwidth
        self.jitter = jitter
        self.packet_loss = packet_loss
        self.latency = latency

    def __repr__(self):
        return (f"LinkMetrics(bandwidth={self.bandwidth}, jitter={self.jitter}, "
                f"packet_loss={self.packet_loss}, latency={self.latency})")


class AlertFlowConditions:
    def __init__(self, cpu_usage, ram_usage, interface_stats, packet_loss, jitter):
        self.cpu_usage = cpu_usage
        self.ram_usage = ram_usage
        self.interface_stats = interface_stats
        self.packet_loss = packet_loss
        self.jitter = jitter

    def __repr__(self):
        return (f"AlertFlowConditions(cpu_usage={self.cpu_usage}, ram_usage={self.ram_usage}, "
                f"interface_stats={self.interface_stats}, packet_loss={self.packet_loss}, jitter={self.jitter})")


class Device:
    def __init__(self, device_id, device_metrics, link_metrics, alertflow_conditions):
        self.device_id = device_id
        self.device_metrics = device_metrics
        self.link_metrics = link_metrics
        self.alertflow_conditions = alertflow_conditions

    def __repr__(self):
        return (f"Device(device_id={self.device_id}, device_metrics={self.device_metrics}, "
                f"link_metrics={self.link_metrics}, alertflow_conditions={self.alertflow_conditions})")


class TaskConfig:
    def __init__(self, task_id, frequency, devices):
        self.task_id = task_id
        self.frequency = frequency
        self.devices = devices

    @classmethod
    def from_json(cls, file_path):
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)

            # Parse general task information
            task_id = data["task_id"]
            frequency = data["frequency"]
            devices = []

            # Parse devices
            for device_data in data["devices"]:
                device_id = device_data["device_id"]

                # Parse device metrics
                dm = device_data["device_metrics"]
                device_metrics = DeviceMetrics(
                    cpu_usage=dm.get("cpu_usage"),
                    ram_usage=dm.get("ram_usage"),
                    interface_stats=dm.get("interface_stats", [])
                )

                # Parse link metrics
                lm = device_data["link_metrics"]
                link_metrics = LinkMetrics(
                    bandwidth=lm.get("bandwidth"),
                    jitter=lm.get("jitter"),
                    packet_loss=lm.get("packet_loss"),
                    latency=lm.get("latency")
                )

                # Parse alertflow conditions
                afc = device_data["alertflow_conditions"]
                alertflow_conditions = AlertFlowConditions(
                    cpu_usage=afc.get("cpu_usage"),
                    ram_usage=afc.get("ram_usage"),
                    interface_stats=afc.get("interface_stats"),
                    packet_loss=afc.get("packet_loss"),
                    jitter=afc.get("jitter")
                )

                # Create Device instance and add to list
                device = Device(
                    device_id=device_id,
                    device_metrics=device_metrics,
                    link_metrics=link_metrics,
                    alertflow_conditions=alertflow_conditions
                )
                devices.append(device)

            # Return the full TaskConfig instance
            return cls(task_id=task_id, frequency=frequency, devices=devices)

        except FileNotFoundError:
            print(f"Error: The file {file_path} was not found.")
            return None
        except json.JSONDecodeError:
            print("Error: The JSON file is not properly formatted.")
            return None

    def __repr__(self):
        return (f"TaskConfig(task_id={self.task_id}, frequency={self.frequency}, "
                f"devices={self.devices})")
