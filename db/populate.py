import xml.etree.ElementTree as ET
import sqlite3
import bcrypt
import os
import getpass
from terminal.data import TerminalData
import os
from webserver.sanitize import InputSanitizer

cwd = os.getcwd()

class NmapToSqlite:
    def __init__(self, db_name):
        data_dir = "{}/db/data/projects/{}/".format(TerminalData.root_dir, TerminalData.current_project)
        self.db_file = "{}{}.db".format(data_dir, db_name)

class NmapToSqlite:
    def __init__(self, cwd):
        self.data_dir = f"{cwd}/db/data/".format(TerminalData.root_dir)

    def parse_nmap_xml(self, xml_file):
        tree = ET.parse(xml_file)
        root = tree.getroot()

        self.results = []

        for host in root.findall(".//host"):
            ip_address = host.find(".//address[@addrtype='ipv4']").attrib['addr']

            ports = []
            for port in host.findall(".//port"):
                port_number = port.attrib['portid']
                service_name = port.find(".//service").attrib.get('name', 'Unknown')
                version = port.find(".//service").attrib.get('version', 'Unknown')
                ports.append({
                    'port': port_number,
                    'service': service_name,
                    'version': version
                })

            self.results.append({
                'ip': ip_address,
                'ports': ports
            })

    def check_duplicate_host(self):
        # Currently unused, might be helpful later
        conn = sqlite3.connect(self.db_file)
        for host in self.results:
            cursor = conn.execute("SELECT ip FROM hosts WHERE ip = ?", (host['ip'],))
            results = cursor.fetchall()
            if results:
                duplicate_ip = results[0][0]
                answer = input("{} already exists in the database, do you wish to update it? (y/n)".format(duplicate_ip))
                if answer.lower() == "n":
                    print(self.results)
                    self.results.remove(host)
                    print(self.results)

    def create_sqlite_db(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hosts (
                id INTEGER PRIMARY KEY,
                ip TEXT NOT NULL,
                port INTEGER NOT NULL,
                service_name TEXT,
                version TEXT,
                UNIQUE(ip, port)
            )
        ''')

        for host_data in self.results:
            for port_data in host_data['ports']:
                cursor.execute("INSERT OR REPLACE INTO hosts (ip, port, service_name, version) VALUES (?, ?, ?, ?)",
                               (host_data['ip'], port_data['port'], port_data['service'], port_data['version']))

        conn.commit()
        conn.close()


class ProjectDb:
    def __init__(self):
        self.project_root_dir = "{}/db/data/projects/".format(TerminalData.root_dir)
        self.default_project_db_file = "{}/db/data/internal/projects.db".format(TerminalData.root_dir)

    def create_sqlite_db(self, name, description, config):
        conn = sqlite3.connect(self.default_project_db_file)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                config TEXT NOT NULL
            )
        ''')
        if self.exists(name):
            print("Project {} already exists in the database, please use a different project name or delete the existing one.".format(name))
            conn.commit()
            conn.close()
            return 0
        cursor.execute("INSERT INTO projects (name, description, config) VALUES (?, ?, ?)",
                    (name, description, config))
        conn.commit()
        conn.close()

    def exists(self, name):
        conn = sqlite3.connect(self.default_project_db_file)
        cursor = conn.cursor()
        results = cursor.execute("SELECT name FROM projects WHERE name = ?", (name,)).fetchall()
        if results:
            return 1
        else:
            return 0

    def list_all_projects(self):
        conn = sqlite3.connect(self.default_project_db_file)
        cursor = conn.execute("SELECT name FROM projects")
        results = cursor.fetchall()
        if results:
            conn.close()
            return results
        else:
            conn.close()
            return [("No projects found... Create one with hihi command!",)] # Don't worry... too lazy

    def delete_project(self, name):
        conn = sqlite3.connect(self.default_project_db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects WHERE name = ?", (name,))
        conn.commit()
        conn.close()

    def get_project_info(self, name):
        conn = sqlite3.connect(self.default_project_db_file)
        cursor = conn.cursor()
        results = cursor.execute("SELECT name, description, config FROM projects WHERE name = ?", (name,)).fetchall()
        conn.close()
        return results

class ManipulateUsers:

    def __init__(self):
        self.data_dir = f"{cwd}/db/data/".format(TerminalData.root_dir)

    def create_database(self):
        # Create the database directory if it doesn't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        data_dir = f"{cwd}/db/data/".format(TerminalData.root_dir)
        data_dir = f'{data_dir}/user.db'

        conn = sqlite3.connect(data_dir)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT NOT NULL,
            role TEXT CHECK (role IN ('admin', 'user')) NOT NULL
            );
        ''')
        conn.commit()
        conn.close()

    def create_admin(self):
        default_user = 'admin'
        default_password = 'admin'
        hashed_password = bcrypt.hashpw(default_password.encode('utf-8'), bcrypt.gensalt())

        data_dir = f"{cwd}/db/data/".format(TerminalData.root_dir)
        data_dir = f'{data_dir}/user.db'

        conn = sqlite3.connect(data_dir)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?) ON CONFLICT(username) DO NOTHING",
                       (default_user, hashed_password.decode('utf-8'), "admin"))
        conn.commit()
        conn.close()

    def create_user(self):
        new_user = input("Enter a username: ")
        new_user = InputSanitizer.sanitize_input(new_user)
        new_user_password = getpass.getpass()
        role = input("Enter the user's role('admin' or 'user'): ").lower()
        if role != 'admin' or 'user':
            print("You must select either 'admin' or 'user'")
        if new_user_password == 'admin':
            print("Password must not be equal to admin")
            exit()
        hashed_password = bcrypt.hashpw(new_user_password.encode('utf-8'), bcrypt.gensalt())
        data_dir = f"{cwd}/db/data/user.db"

        conn = sqlite3.connect(data_dir)
        cursor = conn.cursor()
        cursor.execute(f"INSERT INTO users (username, password, role) VALUES (?, ?, ?) ON CONFLICT(username) DO NOTHING",
                       (new_user, hashed_password.decode('utf-8'), role))
        conn.commit()
        conn.close()
        print(f"Your username is: {new_user}. You can now sign into the webserver.")

    def update_user_password(self):
        user = input("Enter a username: ")
        user = InputSanitizer.sanitize_input(user)
        new_password = getpass.getpass()
        if new_password == 'admin':
            print("Password must not be equal to admin")
            exit()

        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        data_dir = f"{cwd}/db/data/user.db"
        conn = sqlite3.connect(data_dir)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (user,))
        existing_user = cursor.fetchone()

        if not existing_user:
            print(f"User '{user}' not found.")
        else:
            cursor.execute("UPDATE users SET password = ? WHERE username = ?", (hashed_password.decode('utf-8'), user))
            conn.commit()
            print(f"Password for user '{user}' updated successfully.")
        conn.close()

