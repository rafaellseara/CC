class Storage:
    def __init__(self):
        # Initialize dictionaries for in-memory storage
        self.agents = {}       # Store agent information as {agent_id: address}
        self.alerts = []       # Store alerts as a list of alert data
        self.metrics = []      # Store metrics as a list of metrics data

    def store_alert(self, alert):
        """Store an alert in memory."""
        self.alerts.append(alert)
        print(f"Alert stored: {alert}")

    def store_agent(self, agent_id, agent_address):
        """Store an agent in memory."""
        self.agents[agent_id] = agent_address
        print(f"Agent {agent_id} stored with address {agent_address}")

    def store_metrics(self, agent_id, metrics):
        """Store metrics in memory."""
        self.metrics.append({
            "agent_id": agent_id,
            "metrics": metrics
        })
        print(f"Metrics stored for agent {agent_id}: {metrics}")

    def get_alerts(self):
        """Retrieve all stored alerts."""
        return self.alerts

    def get_agents(self):
        """Retrieve all stored agents."""
        return self.agents

    def get_metrics(self):
        """Retrieve all stored metrics."""
        return self.metrics
