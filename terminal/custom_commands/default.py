import sys
import os
from terminal.data import TerminalData
from db import populate
from terminal.utils.project_manager import ProjectManager


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
        file = command.split(" ")[1]  # get file name

    if TerminalData.current_project == "none":
        print("No project currently selected, please use \"project select\" to select one")
        return 0

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


def project_utils(command):
    parts = command.split(" ")

    if len(parts) < 2:
        print("invalid HELP")
        return

    sub_command = parts[1]
    args = parts[2:]

    pm = ProjectManager()
    if sub_command.lower() == "create":
        name = input("Project Name : ")
        description = input("Project Description : ")
        config_path = "should be hardcoded."
        pm.create_project(name, description, config_path)
    elif sub_command.lower() == "delete":
        project = " ".join(args[0:])
        pm.delete_project(project)
    elif sub_command.lower() == "list":
        pm.list_projects()
    elif sub_command.lower() == "select":
        project = " ".join(args[0:])
        print(project)
        pm.select_current_project(project)
    elif sub_command.lower() == "info":
        project = " ".join(args[0:])
        pm.get_project_info(project)