import os
import json
import logging

class Storage:
    """
    A storage class to manage the metrics and other data received from agents.
    """

    def __init__(self, logger=None):
        self.agent_metrics = {}
        self.agent_alerts = {}

        # Use the provided logger or the root logger
        self.logger = logger or logging.getLogger()

############################################################################################################################################################################################

    def store_metrics(self, agent_id, metrics):
        """
        Stores metrics in memory for the specified agent.
        """
        if agent_id not in self.agent_metrics:
            self.agent_metrics[agent_id] = []
        self.agent_metrics[agent_id].append(metrics)
        self.logger.info(f"Metrics stored in memory for agent {agent_id}.")

############################################################################################################################################################################################

    def retrieve_metrics(self, agent_id):
        """
        Retrieves metrics for a specific agent.
        """
        return self.agent_metrics.get(agent_id, [])

############################################################################################################################################################################################

    def store_metrics_in_file(self, agent_id, metrics):
        """
        Stores metrics in a JSON file specific to the agent inside a designated folder.
        """
        # Define the storage folder
        storage_folder = "metrics_storage"
        if not os.path.exists(storage_folder):
            os.makedirs(storage_folder)
            self.logger.info(f"Created storage folder at {storage_folder}.")

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
            self.logger.info(f"Metrics for agent {agent_id} stored in {file_path}.")
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to store metrics for agent {agent_id}: {e}")

############################################################################################################################################################################################

    def store_alerts(self, agent_id, alert):
        """
        Stores alerts in memory for the specified agent.
        """
        if agent_id not in self.agent_alerts:
            self.agent_alerts[agent_id] = []
        self.agent_alerts[agent_id].append(alert)
        self.logger.info(f"Alert stored in memory for agent {agent_id}.")

############################################################################################################################################################################################

    def retrieve_alerts(self, agent_id):
        """
        Retrieves alerts for a specific agent.
        """
        return self.agent_alerts.get(agent_id, [])

############################################################################################################################################################################################

    def store_alerts_in_file(self, agent_id, alert):
        """
        Stores alerts in a JSON file specific to the agent inside a designated folder.
        """
        # Define the storage folder
        storage_folder = "alerts_storage"
        if not os.path.exists(storage_folder):
            os.makedirs(storage_folder)
            self.logger.info(f"Created storage folder at {storage_folder}.")

        # Construct the file path
        file_name = f"agent{agent_id}_alerts.json"
        file_path = os.path.join(storage_folder, file_name)

        # Read existing alerts if the file exists
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as file:
                    existing_alerts = json.load(file)
            except json.JSONDecodeError:
                existing_alerts = []
        else:
            existing_alerts = []

        # Append the new alert
        existing_alerts.append(alert)

        # Write updated alerts back to the file
        try:
            with open(file_path, "w") as file:
                json.dump(existing_alerts, file, indent=4)
            self.logger.info(f"Alert for agent {agent_id} stored in {file_path}.")
        except Exception as e:
            self.logger.error(f"[ERROR] Failed to store alert for agent {agent_id}: {e}")
