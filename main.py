from terminal import CustomShell
from flask import Flask, render_template, request, session, jsonify, redirect
import subprocess
import os
from terminal.data import TerminalData

def start_webserver():
    web_server_command = 'python3 ./webserver/webserver.py'

    # Use os.devnull to redirect both stdout and stderr to /dev/null
    with open(os.devnull, 'w') as null_file:
        # Start the web server as a separate process
        subprocess.Popen(web_server_command, shell=True, stdout=null_file, stderr=subprocess.STDOUT)

if __name__ == '__main__':
    start_webserver()
    shell = CustomShell()
    shell.shell_session()
