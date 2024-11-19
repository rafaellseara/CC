class Storage:
    def __init__(self):
        # Initialize dictionaries for in-memory storage
        self.agents = {}       # Store agent information as {agent_id: address}
        self.alerts = []       # Store alerts as a list of alert data
        self.metrics = []      # Store metrics as a list of metrics data

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
            # Check if agent_data is a dictionary with "device_id" as a key
            if isinstance(agent_data, dict) and agent_data.get("device_id") == device_id:
                return agent_data["address"]
            # If agent_data is a tuple, use indexing
            elif isinstance(agent_data, tuple) and agent_data[0] == device_id:
                return agent_data[1]
        return None
    
    def store_metrics(self, agent_id, metrics):
        self.metrics.append({
            "agent_id": agent_id,
            "metrics": metrics
        })
        print(f"Metrics stored for agent {agent_id}: {metrics}")

    def get_alerts(self):
        return self.alerts

    def get_agents(self):
        return self.agents

    def get_metrics(self):
        return self.metrics
