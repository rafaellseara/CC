# nms_server.py
import json
import threading
from NetTask_Server import start_nettask_server
#from AlertFlow_Server import start_alertflow_server

def load_task_config(file_path="task_config.json"):
    """Carrega a configuração das tarefas a partir de um ficheiro JSON."""
    with open(file_path, 'r') as f:
        config = json.load(f)
    print("Configuração de tarefas carregada:", config)
    return config

def main():
    # Carrega a configuração de tarefas a partir do ficheiro JSON
    task_config = load_task_config()
    
    # Inicia os servidores NetTask e AlertFlow em threads separadas
    nettask_thread = threading.Thread(target=start_nettask_server, args=(task_config,))
    #alertflow_thread = threading.Thread(target=start_alertflow_server)

    nettask_thread.start()
    #alertflow_thread.start()

    print("Servidores NetTask e AlertFlow em execução...")
    nettask_thread.join()
    #alertflow_thread.join()

if __name__ == "__main__":
    main()


'''
import json
import AlertFlow_Server
import NetTask_Server

def load_task_config(file_path):
    with open(file_path, 'r') as file_json:
        config = json.load(file_json)
    return config

task_config = load_task_config("task_config.json") #leu direito
print("Configuração da tarefa carregada:", task_config)
'''
