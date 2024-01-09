from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.styles import Style
import pexpect
import shutil
import os
from terminal.custom_commands import *
from terminal.data import TerminalData


class FileCompleter(Completer):
    """
    A file completer class that generates completions based on files in the current directory.

    Attributes:
        parent (CustomShell): A reference to the parent CustomShell instance.
    """
    def __init__(self, parent):
        self.parent = parent

    def get_completions(self, document, complete_event):
        """
        Generate completions for the given input document.

        Args:
            document (Document): The input document.
            complete_event (CompleteEvent): The completion event.

        Yields:
            Completion: A completion object for a file name.
        """
        prefix = document.get_word_before_cursor()

        for file_name in os.listdir(self.parent.current_directory):
            if file_name.startswith(prefix):
                yield Completion(file_name, -len(prefix))


class CustomShell:
    """
    A custom shell class that provides an interactive command-line interface.

    Attributes:
        current_directory (str): The current working directory.
        custom_style (Style): A custom style for the shell.
        file_completer (FileCompleter): A file completer instance.
        command_history (list): A list to store the command history.
    """
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
        """
        Execute the given command and handle specific commands.

        Args:
            command (str): The command to be executed.

        Returns:
            str or None: The output message or None if no output is needed.
        """
        TerminalData.command_history.append(command)  # Add command to history
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
            file = command.split(" ")[1]
            import_scan(file)

        else:
            try:
                if '~' in command:
                    command = os.path.expanduser(command)

                child = pexpect.spawn(command, encoding='utf-8')

                # Interact with the child process and print its output
                child.expect(pexpect.EOF)
                print(child.before)

                child.close()

            except Exception as e:
                return f"Error executing command: {e}"

    def shell_session(self):
        """
        Start the interactive shell session.
        """
        session = PromptSession(
            completer=self.file_completer,
            complete_while_typing=True,
            style=self.custom_style
        )

        while True:
            try:
                userInput = session.prompt(f'\n┌─[✗]─[{os.getlogin()}@{os.uname().nodename}]─[{self.current_directory}]\n└──╼ $ ')
                output = self.execute_command(userInput)
                if output is not None:
                    print(output)
            except KeyboardInterrupt:
                print("Please type 'exit' to exit.")