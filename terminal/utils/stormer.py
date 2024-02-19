import re
import pexpect
import subprocess
from db.populate import NetStormer
from concurrent.futures import ThreadPoolExecutor
import threading
from terminal.data import TerminalData
import os

file_lock = threading.Lock()  # here for a specific reason, don't know why tho


def run_custom_command_in_thread(command: str, output_path: str):
    print("Starting Thread")
    print(command)
    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(run_command, command, output_path, print_output=False)

        # You can do other things here while the thread is running
        while not future.done():
            # Do something else, or just wait for a while
            pass

        # Wait for the result of the thread (optional)
        result = future.result()


def run_command(command: str, output_file: str, print_output: bool = False) -> None:
    if print_output:
        subprocess.run(command, shell=True, check=True, executable='/bin/bash')
        command_output = "Live command output"  # TODO fix the output capture
    else:
        child = pexpect.spawn(command, encoding='utf-8')

        # Interact with the child process and print its output
        child.expect(pexpect.EOF)
        command_output = child.before
        child.close()

    if output_file:
        with file_lock:
            with open(output_file, 'a', encoding='utf-8') as file:
                file.write("---------\n\n")
                file.write("Command : {}\n".format(command))
                file.write(command_output)
    return None


class Stormer:
    def __init__(self, spray_command: str, re_ip: list[str], re_ports: list[str] | None = None, 
                 all_hosts: bool = False) -> None:
        
        print("ALL HOSTS : {}".format(all_hosts))
        self.spray_command = spray_command
        self.port_list = re_ports
        self.excluded_ips = re_ip
        self.all_hosts = all_hosts
        self.command_output_path = "{}/projects/{}/output/".format(TerminalData.root_dir, TerminalData.current_project)
        self.output_file_path = "{}all_output.txt".format(self.command_output_path)
        if not os.path.exists(self.command_output_path):
            os.mkdir(self.command_output_path)

    def run_live_command(self, live_command: str) -> None:
        print("Running command : {}".format(live_command))
        run_command(live_command, "/home/kyand/NetStormer/test.txt", print_output=True)
        return None

    def spray(self) -> None:
        pattern_ip = r'\{([0-9]{1,3}(?:\.[0-9]{1,3}){3})\}'
        pattern_port = r'\{\s*(\b[0-9]{1,5}\b\s*(,\s*\b[0-9]{1,5}\b\s*)*)\}'

        nt = NetStormer(self.excluded_ips, self.port_list)

        if self.all_hosts:  # if no port provided, spray all hosts
            sprayable_ips_list_of_tuples = nt.get_all_ips()
        else:
            sprayable_ips_list_of_tuples = nt.get_sprayable_ips()  # Returns list of tuples {('ip', port)}

        for ip_port_tuple in sprayable_ips_list_of_tuples:
            for value in ip_port_tuple:  # Need second for loop for multiple ports
                print(ip_port_tuple)
                ip, port = value
                if self.all_hosts:
                    final_command = re.sub(pattern_ip, ip, self.spray_command)
                else:
                    cmd_ip_replaced = re.sub(pattern_ip, ip, self.spray_command)
                    final_command = re.sub(pattern_port, str(port), cmd_ip_replaced)
                print("This cmd will be ran : {}".format(final_command))
                thread = threading.Thread(target=run_custom_command_in_thread, args=(final_command, self.output_file_path))
                thread.start()
        return None
