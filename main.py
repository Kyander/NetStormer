from terminal import CustomShell
from flask import Flask, render_template, request, session, jsonify, redirect
import subprocess
import os

app = Flask(__name__)
def start_webserver():
    #with open(os.devnull, 'w') as null_file:
    #    subprocess.Popen(['gunicorn', '-c', 'webserver/gunicorn_config.py', 'webserver.webserver:app'], stdout=null_file)
    app.run(debug=True)

if __name__ == '__main__':
    start_webserver()
    shell = CustomShell()
    shell.shell_session()
