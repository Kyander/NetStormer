import sys
import os
from terminal.data import TerminalData
from db import populate
from terminal.utils.project_manager import ProjectManager
from terminal.utils.stormer import Stormer
import re


def exit_command() -> None:
    """
    Exists the terminal
    """
    print("Exiting now...")
    sys.exit(1)


def get_history() -> None:
    """
    Prints the command history of the TerminalData.

    This method iterates through the TerminalData's command history and
    prints each command with its corresponding index number.

    Returns:
        None

    Example:
        >>> get_history()
        1: command_1
        2: command_2
        3: command_3
    """
    for idx, cmd in enumerate(TerminalData.command_history, start=1):
        print(f'{idx}: {cmd}')
    return None


def show_scan() -> None:
    if TerminalData.current_project == "none":
        print("Please select a project to run this command : \nproject select [name]")
        return None
    current_project_dir = "{}/db/data/projects/{}/".format(TerminalData.root_dir, TerminalData.current_project)
    print(current_project_dir)
    filenames = [file for file in os.listdir(current_project_dir)
                 if os.path.isfile(os.path.join(current_project_dir, file))]
    print("Please select which scan you wish to see from the list below:")
    for index, filename in enumerate(filenames, start=1):
        print(f"{index}. {filename}")
    selected_index = int(input("Enter the number corresponding to your choice: "))-1
    populate.display_database_data("{}{}".format(current_project_dir, filenames[selected_index]))
    return None


def import_scan(command: str) -> None:
    """
    Imports a nmap xml file and converts it into a SQLite database.

    Args:
        command (str): The command containing the file name to import.

    Returns:
        None
    """
    if " " not in command or "-h" in command:
        print("Please import a nmap xml file :\n    import [nmap.xml]")
        return None
    else:
        file = command.split(" ")[1]  # get file name

    if TerminalData.current_project == "none":
        print("No project currently selected, please use \"project select\" to select one")
        return None

    if os.path.exists(file):
        file_name, file_extension = os.path.splitext(os.path.basename(file))
    else:
        print("File not found.")
        return None
    if file_extension != ".xml":  # TODO add a better check without caring about file extensions
        print("Only xml files from nmap are supported!")
        return None

    print("Creating database...")
    pop = populate.NmapToSqlite(file_name)
    pop.parse_nmap_xml(file)
    pop.create_sqlite_db()
    print("Done!")
    return None


def project_utils(command: str) -> None:
    """
    Args:
        command: A string containing the command to be executed. The command should follow the format "project [sub_command] [arguments]".

    Returns:
        None

    Raises:
        None
    """
    parts = command.split(" ")

    if len(parts) < 2:
        print("Please select one of these options :\n"
              "project (select | create | delete | list | info)")
        return None

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
        if project == "":
            print("Please specify a project to delete :\n"
                  "project delete [name]")
            return None
        pm.delete_project(project)
    elif sub_command.lower() == "list":
        pm.list_projects()
    elif sub_command.lower() == "select":
        project = " ".join(args[0:])
        if project == "":
            print("Please specify a project to select :\n"
                  "project select [name]")
            return None
        print(project)
        pm.select_current_project(project)
    elif sub_command.lower() == "info":
        project = " ".join(args[0:])
        if project == "":
            print("Please specify a project to get info :\n"
                  "project info [name]")
            return None
        pm.get_project_info(project)
    return None


def handle_command_without_ports(spray_command: str, re_ip: list[str], excluded_ips: list[str], pattern_ip: str) -> None:
    live_command = re.sub(pattern_ip, re_ip[0], spray_command)
    excluded_ips.append(re_ip[0])
    s = Stormer(spray_command, excluded_ips, all_hosts=True)
    s.run_live_command(live_command)
    s.spray()
    return None


def handle_command_with_ports(spray_command: str, re_ip: list[str], re_ports: list[str], excluded_ips: list[str], 
                              pattern_ip: str, pattern_port: str, omitted: bool = False) -> None:
    if omitted:
        ports = [port.strip() for port in re_ports]
    else:
        ports = re_ports[0][0].split(",")  # turn tuple into list of ports
        print("port = {}".format(ports))

    replaced = re.sub(pattern_ip, re_ip[0], spray_command)
    # print(replaced)

    live_command = re.sub(pattern_port, ports[0], replaced)
    excluded_ips.append(re_ip[0])
    try:
        s = Stormer(spray_command, excluded_ips, ports)
        s.run_live_command(live_command)
        s.spray()
        return None
    except Exception as e:  # TODO theres probably a better way to check if the command is valid
        print("Invalid Command : {}".format(live_command))
        print("Error : {}".format(str(e)))
        return None


def storm(command: str) -> None:
    """
    Args:
        command (str): The command to be executed by the Stormer object.

    Returns:
        int: Returns 1 if the command execution is successful, otherwise returns 0.
    """

    if TerminalData.current_project == "none":
        print("Please select a project to use this command.")
        return None

    excluded_ips: list[str] = []
    spray_command = " ".join(command.split(" ")[1:])
    pattern_ip = r'\{([0-9]{1,3}(?:\.[0-9]{1,3}){3})\}'
    pattern_port = r'\{\s*(\b[0-9]{1,5}\b\s*(,\s*\b[0-9]{1,5}\b\s*)*)\}'
    re_ports = re.findall(pattern_port, spray_command)  # extract all ports
    re_ip = re.findall(pattern_ip, spray_command)  # only returns something if a match is found for a whole ip

    if not re_ip:
        print("Storm needs to know the location of the ip address, please insert the ip address in the original "
              "command within curly braces as such : storm command {10.10.1.50}")
        return None

    if not re_ports:
        omitted_ports = input("No specified ports were found, do you wish to specify port(s) that will be omitted "
                              "from the commands? (port number(s) or press enter to skip): ")
        omitted_ports_list = omitted_ports.split(',')
        if any(not port.strip().isdigit() for port in omitted_ports_list):  # check if userinput isn't a list of ports
            all_hosts = input("Do you wish to spray this command against all hosts? (y/n): ").lower()
            if all_hosts != "n" and all_hosts != "y":
                print("Invalid answer (y/n)")
                return None
            if all_hosts == "n":
                print("Storm needs to know which port you want to spray against, please provide port(s) like this : "
                      "{80, 8080, 443}")
                return None
            handle_command_without_ports(spray_command, re_ip, excluded_ips, pattern_ip)
            return None
        else:
            handle_command_with_ports(spray_command, re_ip, omitted_ports_list, excluded_ips, pattern_ip, pattern_port, True)
            return None

    handle_command_with_ports(spray_command, re_ip, re_ports, excluded_ips, pattern_ip, pattern_port)
    return None
