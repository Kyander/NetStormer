from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
import subprocess
import shutil
from typing import Optional, Iterable
from prompt_toolkit.formatted_text.base import AnyFormattedText
from prompt_toolkit.document import Document
from terminal.custom_commands import *
from prompt_toolkit.completion import CompleteEvent
from terminal.data import TerminalData
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.completion import NestedCompleter, merge_completers


class LocalPathCompleter(Completer):
    """
    A class used to provide tab-completion for local paths in a text editor.

    Methods:
    - get_completions: Returns an iterable of Completion objects based on the current text document and completion event.
    """

    def get_completions(self, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:

        before = document.text_before_cursor.split()[-1]
        path, partial_name = os.path.split(before)

        if path == "":
            path = "."

        # Ensure the directory exists
        if not os.path.isdir(path):
            return

        for name in os.listdir(path):
            if name.startswith(partial_name):
                yield Completion(
                    name,
                    start_position=-len(partial_name),
                    display=[("bg:ansibrightblue", f"{name}")],
                )


class CustomShell:
    """
    The CustomShell class represents a custom interactive shell session.

    Attributes:
        current_directory (str): The current working directory.
        custom_style (Style): The custom styling for the shell session.
        file_completer (LocalPathCompleter): The file completer for auto-completion.
        custom_command_completer (NestedCompleter): The command completer for auto-completion.

    Methods:
        __init__(self) -> None:
            Initializes the CustomShell object.

        execute_command(self, command: str) -> Optional[str]:
            Executes the given command and handles specific commands.

        shell_session(self) -> None:
            Starts the interactive shell session.
    """
    def __init__(self) -> None:
        terminal_size: os.terminal_size = shutil.get_terminal_size()
        os.environ['COLUMNS'] = str(terminal_size.columns)
        os.environ['LINES'] = str(terminal_size.lines)
        self.current_directory: str = os.getcwd()
        TerminalData.root_dir = self.current_directory
        self.custom_style: Style = Style.from_dict({
            'pygments.comment': '#ansigray',
            'pygments.keyword': '#ansiblue',
            'pygments.operator': '#ansired',
            '': '#ffffff',

            # Prompt.
            'main_line': '#3366FF',
            'project': '#b6ff00 bold',
            'username': '#FF5733 bold',
            'at': '#FF5733 bold',
            'dash': '#75181a',
            'pound': '#ff9900',
            'host': '#FF5733 bold',
            'path': '#ffffff bold',
            'end': '#75181a',
        })

        self.file_completer: LocalPathCompleter = LocalPathCompleter()

        self.custom_command_completer = NestedCompleter.from_nested_dict(
            {
                "show": {"version": None, "clock": None, "ip": {"interface": {"brief": None}}},
                "import": None,
                "project": {"list": None, "create": None, "delete": None, "info": None, "select": None},
                "storm": None,
                "nmap.txt": None,
                "history": None,
                "exit": None,
            }
        )

    def execute_command(self, command: str) -> Optional[str]:
        """
        Execute the given command and handle specific commands.

        Args:
            command (str): The command to be executed.

        Returns:
            str or None: The output message or None if no output is needed.
        """
        TerminalData.command_history.append(command)  # Add command to history
        TerminalData.last_command = command
        actual_command: str = command.split(" ")[0].lower()

        if actual_command == 'cd':
            new_directory: str = ''
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

        elif actual_command == 'ls':
            command = command + ' --color'
            subprocess.run(command, shell=True, executable='/bin/bash')
            pass

        elif actual_command == 'exit':
            exit_command()

        elif actual_command == 'history':
            get_history()

        elif actual_command == "import":
            import_scan(command)

        elif actual_command == "project":
            project_utils(command)

        elif actual_command == "storm":
            storm(command)

        elif actual_command == "nmap.txt":
            show_scan()

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
        return None

    def shell_session(self) -> None:
        """
        Start the interactive shell session.
        """
        session: PromptSession = PromptSession(
            completer=merge_completers([self.file_completer, self.custom_command_completer]),
            complete_while_typing=True,
            style=self.custom_style
        )

        while True:
            try:
                message: Optional[AnyFormattedText] = [
                    ('class:main_line', '\n┌─[✗]─('),
                    ('class:project', '{}'.format(TerminalData.current_project)),
                    ('class:main_line', ')'),
                    ('class:main_line', '-['),
                    ('class:username', '{}'.format(os.getlogin())),
                    ('class:at', '@'),
                    ('class:host', '{}'.format(os.uname().nodename)),
                    ('class:main_line', ']-['),
                    ('class:path', '{}'.format(self.current_directory)),
                    ('class:main_line', ']\n└──╼ '),
                    ('class:pound', '$ '),
                ]

                user_input: str = session.prompt(message)
                output: str | None = self.execute_command(user_input)
                if output is not None:
                    print(output)
            except KeyboardInterrupt:
                print("Please type 'exit' to exit.")
