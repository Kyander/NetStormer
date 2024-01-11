import sys
import os
from terminal.data import TerminalData
from db import populate
def exit_command():
    """
    Exit the shell.

    Prints:
        str: An exit message.
    """
    print("Exiting now...")
    sys.exit(1)

def get_history():
    for idx, cmd in enumerate(TerminalData.command_history, start=1):
        print(f'{idx}: {cmd}')
    return None

def import_scan(command):
    if " " not in command or "-h" in command:
        print("HELP HERE")
        return 0
    else:
        file = command.split(" ")[1]

    if os.path.exists(file):
        file_name, file_extension = os.path.splitext(os.path.basename(file))
    else:
        print("File not found.")
        return None
    if file_extension != ".xml":
        print("Only xml files from nmap are supported!")
        return None

    print("Creating database...")
    pop = populate.NmapToSqlite(file_name)
    pop.parse_nmap_xml(file)
    pop.create_sqlite_db()
    print("Done!")