import json
import os

class Storage:
    def __init__(self, storage_dir='data'):
        # Create the storage directory if it doesn't exist
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
        self.storage_dir = storage_dir
    
    def store_alert(self, alert):
        alert_file = os.path.join(self.storage_dir, 'alerts.json')
        alerts = self._load_data(alert_file)
        alerts.append(alert)
        self._save_data(alert_file, alerts)
    
    def store_agent(self, agent_id, agent_address):
        agent_file = os.path.join(self.storage_dir, 'agents.json')
        agents = self._load_data(agent_file)
        
        if not isinstance(agents, dict):
            agents = {} 

        agents[agent_id] = agent_address
        self._save_data(agent_file, agents)
    
    def store_metrics(self, agent_id, metrics):
        metrics_file = os.path.join(self.storage_dir, 'metrics.json')
        metrics_data = self._load_data(metrics_file)
        metrics_data.append({
            "agent_id": agent_id,
            "metrics": metrics
        })
        self._save_data(metrics_file, metrics_data)
    
    def _load_data(self, file_path):
        """Load data from a JSON file."""
        if not os.path.exists(file_path):
            return []  # Return an empty list if file does not exist
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def _save_data(self, file_path, data):
        """Save data to a JSON file."""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
