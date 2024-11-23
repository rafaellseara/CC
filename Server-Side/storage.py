class Storage:
    def __init__(self):
        self.agents = {}
        self.alerts = []
        self.metrics = []

    def store_alert(self, alert):
        self.alerts.append(alert)
        print(f"Alert stored: {alert}")

    def store_agent(self, agent_id, agent_address):
        self.agents[agent_id] = {"device_id": agent_id, "address": agent_address}
        print(f"Agent {agent_id} stored with address {agent_address}")

    def get_agents(self):
        return self.agents

    def get_agent_address_by_device_id(self, device_id):
        for agent_id, agent_data in self.agents.items():
            if isinstance(agent_data, dict) and agent_data.get("device_id") == device_id:
                return agent_data["address"]
        return None

    def store_metrics(self, agent_id, metrics):
        self.metrics.append({"agent_id": agent_id, "metrics": metrics})
        print(f"Metrics stored for agent {agent_id}: {metrics}")

    def get_alerts(self):
        return self.alerts

    def get_metrics(self):
        return self.metrics
