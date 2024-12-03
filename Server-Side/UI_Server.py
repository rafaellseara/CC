import curses
import os
import json


class UIServer:
    def __init__(self, server_from_NMS):
        self.server = server_from_NMS  # Reference to the NMS_Server instance

    def run_curses_ui(self, stdscr):
        curses.curs_set(1)
        stdscr.clear()

        curses.start_color()

        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)

        def prompt_config_path():
            curses.echo()
            main_directory = os.getcwd()

            while True:
                stdscr.clear()
                stdscr.addstr(0, 0, "=== NMS Server ===", curses.A_BOLD)
                stdscr.addstr(2, 0, "Enter the name of the config file: ")
                config_file = stdscr.getstr(2, 35).decode("utf-8").strip()

                config_path = os.path.join(main_directory, config_file)

                if (os.path.exists(config_path) and config_path.endswith(".json")):
                    self.server.task_path = config_file
                    stdscr.addstr(4, 0, f"Config file found: {config_path}", curses.A_DIM)
                    stdscr.addstr(5, 0, "Press any key to continue...")
                    stdscr.getch()
                    break
                else:
                    stdscr.addstr(4, 0, "Invalid json file or not found in the main directory. Please try again.", curses.A_BOLD)
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
        Displays the message log from the NMS server with pagination and line wrapping.
        Includes an option to update the logs with 'u' key.
        """
        # Function to update logs
        def update_logs():
            raw_logs = self.server.get_logs()
            logs = raw_logs.split("\n") if raw_logs else ["No logs available."]
            return logs

        # Initial log loading
        logs = update_logs()

        max_y, max_x = stdscr.getmaxyx()

        # Dimensions for the content area
        title = "Message Log"
        footer = "Press 'n' for next page, 'p' for previous, 'u' to update, or 'q' to quit."
        header_lines = 2
        footer_lines = 2
        content_height = max_y - header_lines - footer_lines

        # Wrap lines that exceed terminal width
        wrapped_logs = []
        for log in logs:
            while len(log) > max_x:  # Split long lines into parts that fit terminal width
                wrapped_logs.append(log[:max_x])
                log = log[max_x:]
            wrapped_logs.append(log)  # Add any remaining part of the log

        # Paginate wrapped logs
        pages = [wrapped_logs[i:i + content_height] for i in range(0, len(wrapped_logs), content_height)]
        current_page = 0

        while True:
            stdscr.clear()

            # Display title
            try:
                stdscr.addstr(0, 0, title.center(max_x), curses.A_BOLD)
            except curses.error:
                pass  # Ignore errors caused by insufficient terminal size

            # Display content for the current page
            for i, log in enumerate(pages[current_page]):
                line_y = i + 1
                if line_y >= max_y - footer_lines:
                    break
                try:
                    stdscr.addstr(line_y, 0, log)  # No truncation needed since logs are already wrapped
                except curses.error:
                    pass

            # Display footer
            page_info = f"Page {current_page + 1}/{len(pages)}"
            try:
                stdscr.addstr(max_y - 2, 0, page_info.ljust(max_x), curses.color_pair(1))
                stdscr.addstr(max_y - 1, 0, footer.ljust(max_x), curses.color_pair(1))
            except curses.error:
                pass

            stdscr.refresh()

            # Handle user input for navigation
            key = stdscr.getch()

            if key in (ord('q'), ord('Q')):  # Quit
                break
            elif key in (ord('n'), ord('N')) and current_page < len(pages) - 1:  # Next page
                current_page += 1
            elif key in (ord('p'), ord('P')) and current_page > 0:  # Previous page
                current_page -= 1
            elif key in (ord('u'), ord('U')):  # Update logs
                logs = update_logs()
                wrapped_logs = []
                for log in logs:
                    while len(log) > max_x:
                        wrapped_logs.append(log[:max_x])
                        log = log[max_x:]
                    wrapped_logs.append(log)
                pages = [wrapped_logs[i:i + content_height] for i in range(0, len(wrapped_logs), content_height)]
                current_page = 0  # Reset to the first page after updating

    def view_storage(self, stdscr):
        """
        Displays stored metrics for a selected agent from the `metrics_storage` folder.
        Includes a menu to choose between Agent 1 and Agent 2.
        """

        def load_metrics(agent_id):
            """
            Loads metrics for a specific agent from the `metrics_storage` folder.
            """
            storage_folder = "metrics_storage"
            file_name = f"agent{agent_id}_metrics_collected.json"
            file_path = os.path.join(storage_folder, file_name)

            if not os.path.exists(file_path):
                return f"Metrics file for Agent {agent_id} not found."

            try:
                with open(file_path, "r") as file:
                    return json.load(file)
            except json.JSONDecodeError as e:
                return f"Error decoding JSON for Agent {agent_id}: {e}"
            except Exception as e:
                return f"Error reading file for Agent {agent_id}: {e}"

        def format_metrics(metrics, indent=0):
            """
            Recursively formats metrics for better readability.
            """
            formatted = []
            for entry in metrics:
                if isinstance(entry, dict):
                    for key, value in entry.items():
                        formatted.append(" " * indent + f"{key}:")
                        if isinstance(value, dict):
                            formatted.extend(format_metrics([value], indent + 4))
                        elif isinstance(value, list):
                            for item in value:
                                formatted.append(" " * (indent + 4) + str(item))
                        else:
                            formatted.append(" " * (indent + 4) + str(value))
                else:
                    formatted.append(" " * indent + str(entry))
            return formatted

        def display_menu(stdscr, options, title="Select an Option"):
            """
            Displays a menu and allows the user to choose an option.
            """
            current_index = 0
            while True:
                stdscr.clear()
                max_y, max_x = stdscr.getmaxyx()
                stdscr.addstr(0, 0, title.center(max_x), curses.A_BOLD)
                for i, option in enumerate(options):
                    if i == current_index:
                        stdscr.addstr(i + 2, 0, f"> {option}", curses.A_REVERSE)
                    else:
                        stdscr.addstr(i + 2, 0, f"  {option}")
                stdscr.refresh()

                key = stdscr.getch()
                if key in (ord('q'), ord('Q')):  # Quit
                    return None
                elif key in (curses.KEY_UP, ord('k')) and current_index > 0:  # Up
                    current_index -= 1
                elif key in (curses.KEY_DOWN, ord('j')) and current_index < len(options) - 1:  # Down
                    current_index += 1
                elif key in (ord('\n'), ord('\r')):  # Enter
                    return options[current_index]

        # Menu to select agent
        agent_id = display_menu(stdscr, ["Agent 1 Metrics", "Agent 2 Metrics"], "Select Agent")
        if not agent_id:
            return

        # Extract agent number
        agent_number = agent_id.split()[1]

        # Load metrics for the selected agent
        metrics = load_metrics(agent_number)

        # Check if an error occurred
        if isinstance(metrics, str):  # Error message
            content = [metrics]
        else:
            content = format_metrics(metrics)

        # Paginate and display metrics
        max_y, max_x = stdscr.getmaxyx()
        content_height = max_y - 4
        pages = [content[i:i + content_height] for i in range(0, len(content), content_height)]
        current_page = 0

        while True:
            stdscr.clear()

            # Display the header
            try:
                stdscr.addstr(0, 0, f"{agent_id} - Stored Metrics".center(max_x), curses.A_BOLD)
            except curses.error:
                pass

            # Display the content for the current page
            for i, line in enumerate(pages[current_page]):
                try:
                    stdscr.addstr(i + 2, 0, line[:max_x])  # Truncate to terminal width
                except curses.error:
                    pass

            # Footer with navigation options
            footer = "Press 'n' for next page, 'p' for previous, or 'q' to quit."
            page_info = f"Page {current_page + 1}/{len(pages)}"
            try:
                stdscr.addstr(max_y - 2, 0, page_info.ljust(max_x), curses.color_pair(1))
                stdscr.addstr(max_y - 1, 0, footer.ljust(max_x), curses.color_pair(1))
            except curses.error:
                pass

            stdscr.refresh()

            # Handle user input
            key = stdscr.getch()
            if key in (ord('q'), ord('Q')):  # Quit
                break
            elif key in (ord('n'), ord('N')) and current_page < len(pages) - 1:  # Next page
                current_page += 1
            elif key in (ord('p'), ord('P')) and current_page > 0:  # Previous page
                current_page -= 1

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