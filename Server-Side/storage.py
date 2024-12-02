import os
import json

class Storage:
    """
    A storage class to manage the metrics and other data received from agents.
    """

    def __init__(self):
        self.agent_metrics = {}

    def store_metrics(self, agent_id, metrics):
        """
        Stores metrics in memory for the specified agent.
        """
        if agent_id not in self.agent_metrics:
            self.agent_metrics[agent_id] = []
        self.agent_metrics[agent_id].append(metrics)
        print(f"[INFO] Metrics stored in memory for agent {agent_id}.")

    def retrieve_metrics(self, agent_id):
        """
        Retrieves metrics for a specific agent.
        """
        return self.agent_metrics.get(agent_id, [])

    @staticmethod
    def store_metrics_in_file(agent_id, metrics):
        """
        Stores metrics in a JSON file specific to the agent inside a designated folder.
        """
        # Define the storage folder
        storage_folder = "metrics_storage"
        if not os.path.exists(storage_folder):
            os.makedirs(storage_folder)
            print(f"[INFO] Created storage folder at {storage_folder}.")

        # Construct the file path
        file_name = f"agent{agent_id}_metrics_collected.json"
        file_path = os.path.join(storage_folder, file_name)

        # Read existing metrics if the file exists
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as file:
                    existing_metrics = json.load(file)
            except json.JSONDecodeError:
                existing_metrics = []
        else:
            existing_metrics = []

        # Append the new metrics
        existing_metrics.append(metrics)

        # Write updated metrics back to the file
        try:
            with open(file_path, "w") as file:
                json.dump(existing_metrics, file, indent=4)
            print(f"[INFO] Metrics for agent {agent_id} stored in {file_path}.")
        except Exception as e:
            print(f"[ERROR] Failed to store metrics for agent {agent_id}: {e}")

