import json
import threading
from NetTask_Server import start_nettask_server
from AlertFlow_Server import start_alertflow_server

def load_task_config(file_path="task_config.json"):
    with open(file_path, 'r') as f:
        config = json.load(f)
    print("Task configuration loaded:", config)
    return config

def main():
    task_config = load_task_config()
    
    nettask_thread = threading.Thread(target=start_nettask_server, args=(task_config,))
    alertflow_thread = threading.Thread(target=start_alertflow_server)

    nettask_thread.start()
    alertflow_thread.start()

    print("NetTask and AlertFlow servers are running...")
    nettask_thread.join()
    alertflow_thread.join()

if __name__ == "__main__":
    main()
