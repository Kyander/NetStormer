from typing import List


class TerminalData:
    command_history: List[str] = []
    last_command = ""
    root_dir = ""
    current_project = "none"
