from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.styles import Style
import shutil
import os
import subprocess
from terminal.custom_commands import *
from terminal.data import TerminalData

class FileCompleter(Completer):
    def __init__(self, parent):
        self.parent = parent

    def get_completions(self, document, complete_event):
        prefix = document.get_word_before_cursor()

        for file_name in os.listdir(self.parent.current_directory):
            if file_name.startswith(prefix):
                yield Completion(file_name, -len(prefix))

class CustomShell:
    def __init__(self):
        terminal_size = shutil.get_terminal_size()
        os.environ['COLUMNS'] = str(terminal_size.columns)
        os.environ['LINES'] = str(terminal_size.lines)
        self.current_directory = os.getcwd()
        TerminalData.root_dir = self.current_directory
        self.custom_style = Style.from_dict({
            'pygments.comment': '#ansigray',
            'pygments.keyword': '#ansiblue',
            'pygments.operator': '#ansired'
        })
        self.file_completer = FileCompleter(self)

    def execute_command(self, command):
        TerminalData.command_history.append(command)
        TerminalData.last_command = command
        actual_command = command.split(" ")[0].lower()

        if actual_command == 'cd':
            try:
                new_directory = command[3:]
                if '~' in new_directory:
                    new_directory = os.path.expanduser(new_directory)
                os.chdir(new_directory)
                self.current_directory = os.getcwd()
            except FileNotFoundError:
                return f"Directory not found: {new_directory}"
            except Exception as e:
                return f"Error changing directory: {e}"

        elif actual_command == 'exit':
            exit_command()

        elif actual_command == 'history':
            get_history()

        elif actual_command == "import":
            import_scan(command)

        elif actual_command == "project":
            project_utils(command)

        else:
            try:
                if '~' in command:
                    command = os.path.expanduser(command)
                # Use subprocess to spawn a Bash shell
                subprocess.run(command, shell=True, check=True, executable='/bin/bash')

            except subprocess.CalledProcessError as e:
                error_message = f"Command failed with return code {e.returncode}: "
                if e.output is not None:
                    error_message += e.output.decode()
                else:
                    error_message += "No output available."
                return error_message
            except Exception as e:
                return f"Error executing command: {e}"

    def shell_session(self):
        session = PromptSession(
            completer=self.file_completer,
            complete_while_typing=True,
            style=self.custom_style
        )

        while True:
            try:
                userInput = session.prompt(f'\n┌─[✗]─({TerminalData.current_project})[{os.getlogin()}@{os.uname().nodename}]─[{self.current_directory}]\n└──╼ $ ')
                output = self.execute_command(userInput)

                if output is not None:
                    print(output)
            except KeyboardInterrupt:
                print("Please type 'exit' to exit.")
