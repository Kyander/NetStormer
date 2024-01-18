import sys
import os
from terminal.data import TerminalData
from db import populate
from terminal.utils.project_manager import ProjectManager
from terminal.utils.stormer import Stormer
import pexpect
import re
import threading


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

def show_scan():
    if TerminalData.current_project == "none":
        print("Please select a project to run this command")
        return 0
    current_project_dir = "{}/db/data/projects/{}/".format(TerminalData.root_dir, TerminalData.current_project)
    print(current_project_dir)
    filenames = [file for file in os.listdir(current_project_dir) if os.path.isfile(os.path.join(current_project_dir, file))]
    print("Please select which scan you wish to see from the list below:")
    for index, filename in enumerate(filenames, start=1):
        print(f"{index}. {filename}")
    selected_index = int(input("Enter the number corresponding to your choice: "))-1
    populate.display_database_data("{}{}".format(current_project_dir, filenames[selected_index]))


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


def storm(command):
    if TerminalData.current_project == "none":
        print("Please select a project to use this command.")
        return 0
    excluded_ips = []
    spray_command = " ".join(command.split(" ")[1:])
    pattern_ip = r'\{([0-9]{1,3}(?:\.[0-9]{1,3}){3})\}'
    pattern_port = r'\{\s*(\b[0-9]{1,5}\b\s*(,\s*\b[0-9]{1,5}\b\s*)*)\}'
    re_ports = re.findall(pattern_port, spray_command)  # extract all ports
    re_ip = re.findall(pattern_ip,
                       spray_command)  # re_ip != the actual ip, but only returns something if a match is found for a whole ip
    # print(re_ip)
    if not re_ip:
        print(
            "Storm needs to know the location of the ip address, please insert the ip address in the original command within curly braces as such : {10.10.1.50}")
        return 0
    if not re_ports:
        print(
            "Storm needs to know which port you want to spray against, please provide ports like this : {80, 8080, 443}")
        return 0

    ports = re_ports[0][0].split(",")  # turn tuple into list of ports
    # print("port = {}".format(ports))
    replaced = re.sub(pattern_ip, re_ip[0], spray_command)
    # print(replaced)

    live_command = re.sub(pattern_port, ports[0], replaced)
    excluded_ips.append(re_ip[0])

    nt = Stormer(spray_command, ports, excluded_ips)
    nt.run_live_command(live_command)
    nt.spray()
