import curses
import os

class UIServer:
    def __init__(self, server_from_NMS):
        self.server = server_from_NMS  # Reference to the NMS_Server instance

    def run_curses_ui(self, stdscr):
        curses.curs_set(1)
        stdscr.clear()

        def prompt_config_path():
            curses.echo()
            main_directory = os.getcwd()

            while True:
                stdscr.clear()
                stdscr.addstr(0, 0, "=== NMS Server ===", curses.A_BOLD)
                stdscr.addstr(2, 0, "Enter the name of the config file: ")
                config_file = stdscr.getstr(2, 35).decode("utf-8").strip()

                config_path = os.path.join(main_directory, config_file)

                if os.path.exists(config_path):
                    self.server.task_path = config_file
                    stdscr.addstr(4, 0, f"Config file found: {config_path}", curses.A_DIM)
                    stdscr.addstr(5, 0, "Press any key to continue...")
                    stdscr.getch()
                    break
                else:
                    stdscr.addstr(4, 0, "Invalid file or not found in the main directory. Please try again.", curses.A_BOLD)
                    stdscr.addstr(5, 0, "Press any key to retry...")
                    stdscr.getch()

            curses.noecho()

        prompt_config_path()

        menu = [
            "View Message Log",
            "View Storage",
            "View Registered Agents",
            "Exit"
        ]
        selected_index = 0

        while True:
            stdscr.clear()
            stdscr.addstr(0, 0, "=== NMS Server ===", curses.A_BOLD)
            stdscr.addstr(1, 0, f"Config File Path: {self.server.task_path}", curses.A_DIM)
            stdscr.addstr(3, 0, "Use Arrow Keys to navigate and Enter to select.\n")

            for i, item in enumerate(menu):
                if i == selected_index:
                    stdscr.addstr(4 + i, 2, f"> {item}", curses.A_REVERSE)
                else:
                    stdscr.addstr(4 + i, 2, f"  {item}")

            key = stdscr.getch()

            if key == curses.KEY_UP and selected_index > 0:
                selected_index -= 1
            elif key == curses.KEY_DOWN and selected_index < len(menu) - 1:
                selected_index += 1
            elif key == curses.KEY_ENTER or key in [10, 13]:
                if menu[selected_index] == "View Message Log":
                    self.view_message_log(stdscr)
                elif menu[selected_index] == "View Storage":
                    self.view_storage(stdscr)
                elif menu[selected_index] == "View Registered Agents":
                    self.view_registered_agents(stdscr)
                elif menu[selected_index] == "Exit":
                    break

    def view_message_log(self, stdscr):
        """
        Displays the message log from the NMS server.
        """
        logs = self.server.get_logs()
        content = logs if logs else "No logs available."
        self.display_popup(stdscr, "Message Log", content)

    def view_storage(self, stdscr):
        """
        Displays stored metrics.
        """
        content = ""
        for agent_id, metrics in self.server.storage.agent_metrics.items():
            content += f"Agent {agent_id} Metrics:\n"
            for metric in metrics:
                content += f"  {metric}\n"
            content += "\n"
        if not content:
            content = "No metrics stored yet."
        self.display_popup(stdscr, "Storage", content)

    def view_registered_agents(self, stdscr):
        """
        Displays registered agents.
        """
        content = "\n".join(
            [f"Agent {agent_id}: {addr}" for agent_id, addr in self.server.net_task.registered_agents.items()]
        )
        if not content:
            content = "No agents registered yet."
        self.display_popup(stdscr, "Registered Agents", content)

    def display_popup(self, stdscr, title, content):
        """
        Displays a popup window with the provided content.
        """
        stdscr.clear()
        stdscr.addstr(0, 0, f"=== {title} ===\n")
        stdscr.addstr(2, 0, content)
        stdscr.addstr(20 + content.count("\n"), 0, "Press any key to return.")
        stdscr.refresh()
        stdscr.getch()