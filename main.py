from terminal import CustomShell
import subprocess
import os
from db.populate import ManipulateUsers

def start_webserver():
    web_server_command = 'python3 webserver/webserver.py'

    # Use os.devnull to redirect both stdout and stderr to /dev/null
    with open(os.devnull, 'w') as null_file:
        # Start the web server as a separate process
        subprocess.Popen(web_server_command, shell=True, stdout=null_file, stderr=subprocess.STDOUT)


if __name__ == '__main__':
    start_webserver()
    admin_user = ManipulateUsers()
    admin_user.create_database()
    admin_user.create_admin()

    shell = CustomShell()
    shell.shell_session()


