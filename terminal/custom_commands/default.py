import sys
from terminal.data import TerminalData
def exit_command():
    """
    Exit the shell.

    Prints:
        str: An exit message.
    """
    print("Exiting now...")
    sys.exit(1)

def get_history():
    # Print command history stored in the script
    for idx, cmd in enumerate(TerminalData.command_history, start=1):
        print(f'{idx}: {cmd}')
    return None  # Don't print 'None' for history command