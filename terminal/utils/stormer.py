import re
import pexpect
from db.populate import NetStormer
from concurrent.futures import ThreadPoolExecutor
import threading
from terminal.data import TerminalData
import os

file_lock = threading.Lock()
def run_custom_command_in_thread(command, output_path, print_output):
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

def run_command(command, output_file, print_output=False):
    child = pexpect.spawn(command, encoding='utf-8')

    # Interact with the child process and print its output
    child.expect(pexpect.EOF)
    command_output = child.before
    if print_output:
        print(command_output)
    child.close()
    if output_file:
        with file_lock:
            with open(output_file, 'a', encoding='utf-8') as file:
                file.write("---------\n\n")
                file.write("Command : {}\n".format(command))
                file.write(command_output)

class Stormer:
    def __init__(self, spray_command, re_ports, re_ip):
        self.spray_command = spray_command
        self.port_list = re_ports
        self.excluded_ips = re_ip
        self.command_ouput_path = "{}/projects/{}/output/".format(TerminalData.root_dir, TerminalData.current_project)
        self.output_file_path = "{}all_output.txt".format(self.command_ouput_path)
        if not os.path.exists(self.command_ouput_path):
            os.mkdir(self.command_ouput_path)
    def run_live_command(self, live_command):
        print("Running command : {}".format(live_command))
        run_command(live_command, "/home/kyand/NetStormer/test.txt", print_output=True)
    def spray(self):
        pattern_ip = r'\{([0-9]{1,3}(?:\.[0-9]{1,3}){3})\}'
        pattern_port = r'\{\s*(\b[0-9]{1,5}\b\s*(,\s*\b[0-9]{1,5}\b\s*)*)\}'
        a = NetStormer(self.excluded_ips, self.port_list)
        test = a.get_sprayable_ips()
        for z in test:
            for x in z:
                replaced = re.sub(pattern_ip, x[0], self.spray_command)
                replaced2 = re.sub(pattern_port, str(x[1]), replaced)
                #print("This cmd will be ran : {}".format(replaced2))
                thread = threading.Thread(target=run_custom_command_in_thread, args=(replaced2, self.output_file_path, False))
                thread.start()