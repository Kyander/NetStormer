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
    # Print command history stored in the script
    for idx, cmd in enumerate(TerminalData.command_history, start=1):
        print(f'{idx}: {cmd}')
    return None  # Don't print 'None' for history command

def import_scan(file):
    if os.path.exists(file):
        file_name, file_extension = os.path.splitext(os.path.basename(file))
    else:
        print("File not found.")
        return None
    if file_extension != ".xml":
        print("Only xml files from nmap are supported!")
        return None

    print("Creating database...")
    pop = populate.NmapToSqlite()
    pop.parse_nmap_xml(file)
    pop.create_sqlite_db(file_name)
    print("Done!")