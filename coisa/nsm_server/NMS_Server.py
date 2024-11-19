import json
import threading
import sys
import socket
#from NetTask_Server import start_nettask_server
#from AlertFlow_Server import start_alertflow_server

class nms_server():

    def __init__(self, port):
        self.name = socket.gethostname()                                        # Obtém o hostname da máquina
        self.port = int(port)                                                   # Número da porta onde o servidor será configurado.
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   # Cria um socket para comunicação via IPv4 e protocolo UDP
        self.server_socket.bind((socket.gethostbyname(self.name), self.port))   # Vincula o socket ao endereço IP correspondente ao hostname e à porta

    def load_task_config(self,file_path="task_config.json"):
        print("Loading task configuration...")
        with open(file_path, 'r') as f:
            config = json.load(f)
        print("Task configuration loaded")
        return config
    
    # start_connections: wait for the connections with the agents and handle the connections
    def start_connections(self, task_config):
        print(f"Servidor ativo em {self.server_socket.getsockname()[0]} porta {self.port}")
        try:
            while True:
                data, address_node = self.server_socket.recvfrom(1024)
                #print(f"Dados recebidos: {data}, Endereço: {address_node}")
                #name_node = socket.gethostbyaddr(address_node[0])[0][:-20]

                print(f"O Agente {address_node[0]} conectou-se ao servidor")

                message = data.decode('utf-8')  # Decodifica os bytes para string
                print(f"Mensagem recebida: {message}")
                # create a thread to handle the connection with the node
                #thread_node = threading.Thread(target=start_nettask_server, args=(task_config, data))    
                #thread_node.start()
                
        except KeyboardInterrupt:
            print("\nServer disconnected")
            self.server_socket.close()
            sys.exit(0)

    def main(self):
        task_config = nms_server.load_task_config(self)

        nms_server.start_connections(self, task_config)
        
        #nettask_thread = threading.Thread(target=start_nettask_server, args=(task_config,))
        #alertflow_thread = threading.Thread(target=start_alertflow_server)

        #nettask_thread.start()
        #alertflow_thread.start()

        #print("NetTask and AlertFlow servers are running...")
        #nettask_thread.join()
        #alertflow_thread.join()

if __name__ == "__main__":
    server = nms_server(5005)
    server.main()
