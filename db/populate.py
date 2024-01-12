import xml.etree.ElementTree as ET
import sqlite3
import bcrypt
import os
import getpass
from terminal.data import TerminalData
from webserver.sanitize import InputSanitizer

cwd = os.getcwd()

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

    def create_sqlite_db(self, db_name):
        data_dir = "{}{}".format(self.data_dir, db_name)
        print(data_dir)
        conn = sqlite3.connect(data_dir)
        cursor = conn.cursor()

        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hosts (
                id INTEGER PRIMARY KEY,
                ip TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS open_ports (
                id INTEGER PRIMARY KEY,
                host_id INTEGER,
                port INTEGER NOT NULL,
                service_name TEXT,
                version TEXT,
                FOREIGN KEY (host_id) REFERENCES hosts (id)
            )
        ''')

        # Insert data
        for host_data in self.results:
            cursor.execute("INSERT INTO hosts (ip) VALUES (?)", (host_data['ip'],))
            host_id = cursor.lastrowid

            for port_data in host_data['ports']:
                cursor.execute("INSERT INTO open_ports (host_id, port, service_name, version) VALUES (?, ?, ?, ?)",
                               (host_id, port_data['port'], port_data['service'], port_data['version']))

        # Commit changes and close connection
        conn.commit()
        conn.close()


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

