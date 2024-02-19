import xml.etree.ElementTree as ET
import sqlite3
import bcrypt
import getpass
import os
from webserver.sanitize import InputSanitizer
from terminal.data import TerminalData

class NmapToSqlite:
    def __init__(self, db_name: str) -> None:
        data_dir = "{}/db/data/projects/{}/".format(TerminalData.root_dir, TerminalData.current_project)
        self.db_file = "{}{}.db".format(data_dir, db_name)
        self.results: list[dict[str, str | None | list[dict[str, str]]]] = []

    def parse_nmap_xml(self, xml_file: str) -> None:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        for host in root.findall(".//host"):
            address_element = host.find(".//address[@addrtype='ipv4']")
            ip_address = address_element.attrib['addr'] if address_element is not None else None

            ports: list[dict[str, str]] = []
            for port in host.findall(".//port"):
                port_number = port.attrib['portid']
                service_element = port.find(".//service")
                service_name = service_element.attrib.get('name', 'Unknown') if service_element is not None else 'Unknown'
                service_element = port.find(".//service") if port is not None else None
                version = service_element.attrib.get('version', 'Unknown') if service_element is not None else 'Unknown'
                ports.append({
                    'port': port_number,
                    'service': service_name,
                    'version': version
                })

            self.results.append({
                'ip': ip_address,
                'ports': ports
            })
            return None

    def check_duplicate_host(self) -> None:
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
        return None

    def create_sqlite_db(self) -> None:
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
            if isinstance(host_data['ports'], list):
                for port_data in host_data['ports']:
                    cursor.execute("INSERT OR REPLACE INTO hosts (ip, port, service_name, version) VALUES (?, ?, ?, ?)",
                                   (host_data['ip'], port_data['port'], port_data['service'], port_data['version']))
            else:
                raise ValueError("Invalid type for host_data['ports']")

        conn.commit()
        conn.close()
        return None


class ProjectDb:
    def __init__(self) -> None:
        self.project_root_dir = "{}/db/data/projects/".format(TerminalData.root_dir)
        self.default_project_db_file = "{}/db/data/internal/projects.db".format(TerminalData.root_dir)

    def create_sqlite_db(self, name: str, description: str, config: str) -> None:
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
            return None
        cursor.execute("INSERT INTO projects (name, description, config) VALUES (?, ?, ?)",
                    (name, description, config))
        conn.commit()
        conn.close()
        return None

    def exists(self, name: str) -> bool:
        conn = sqlite3.connect(self.default_project_db_file)
        cursor = conn.cursor()
        results = cursor.execute("SELECT name FROM projects WHERE name = ?", (name,)).fetchall()
        if results:
            return True
        else:
            return False

    def list_all_projects(self) -> list[tuple[str]]:
        conn = sqlite3.connect(self.default_project_db_file)
        cursor = conn.execute("SELECT name FROM projects")
        results = cursor.fetchall()
        if results:
            conn.close()
            return results
        else:
            conn.close()
            return [("No projects found... Create one with hihi command!",)] # Don't worry... too lazy

    def delete_project(self, name: str) -> None:
        conn = sqlite3.connect(self.default_project_db_file)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM projects WHERE name = ?", (name,))
        conn.commit()
        conn.close()
        return None

    def get_project_info(self, name: str) -> list[tuple[str]]:
        conn = sqlite3.connect(self.default_project_db_file)
        cursor = conn.cursor()
        results = cursor.execute("SELECT name, description, config FROM projects WHERE name = ?", (name,)).fetchall()
        conn.close()
        return results


class NetStormer:
    def __init__(self, excluded_ips: list[str], ports: list[str] | None) -> None:
        self.current_project_db_dir = "{}/db/data/projects/{}/".format(TerminalData.root_dir, TerminalData.current_project)
        all_files = os.listdir(self.current_project_db_dir)
        self.scan_files = [file for file in all_files if file.endswith(".db")]
        self.excluded_ips = excluded_ips
        self.ports = ports

    def get_sprayable_ips(self) -> list[list[tuple[str, int | None]]]:  # TODO INSPECT CODE FLOW PLEASE, NOT SURE IF THERE ARE BUGS
        sprayable_ips = []
        for scan in self.scan_files:
            conn = sqlite3.connect("{}{}".format(self.current_project_db_dir, scan))
            cursor = conn.cursor()
            #print(self.ports)
            if self.ports is None:
                query = "SELECT DISTINCT ip, NULL FROM hosts"
                results = cursor.execute(query).fetchall()
                #print(results)
            else:
                query = "SELECT ip, port FROM hosts WHERE port IN ({})".format(','.join(['?'] * len(self.ports)))
                results = cursor.execute(query, self.ports).fetchall()
            sprayable_ips.append(results)
        print("HIHIHIIH: {}".format(sprayable_ips))
        return sprayable_ips

    def get_all_ips(self) -> list[list[tuple[str, None]]]:  # TODO Probably can be removed, as the function above does this.
        all_ips = []
        for scan in self.scan_files:
            conn = sqlite3.connect("{}{}".format(self.current_project_db_dir, scan))
            cursor = conn.cursor()
            query = "SELECT DISTINCT ip, NULL FROM hosts"
            results = cursor.execute(query).fetchall()
            all_ips.append(results)

        return all_ips


def display_database_data(database_path: str) -> None:
    try:
        # Connect to the SQLite database
        connection = sqlite3.connect(database_path)
        cursor = connection.cursor()

        # Execute a SELECT query to fetch all rows from the table
        cursor.execute("SELECT * FROM hosts")
        rows = cursor.fetchall()

        # Display the header
        print("{:<5} {:<15} {:<10} {:<20} {:<15}".format("ID", "IP", "Port", "Service Name", "Version"))
        print("="*65)

        # Display each row
        for row in rows:
            print("{:<5} {:<15} {:<10} {:<20} {:<15}".format(*row))

    except sqlite3.Error as e:
        print("Error accessing the database:", e)
        return None

    finally:
        # Close the database connection
        if connection:
            connection.close()
            return None
        return None


class ManipulateUsers:

    def __init__(self):
        self.data_dir = "{}db/data/".format(TerminalData.root_dir)

    def create_database(self):
        # Create the database directory if it doesn't exist
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        data_dir = "{}db/data/user.db".format(TerminalData.root_dir)

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

        data_dir = "{}db/data/user.db".format(TerminalData.root_dir)

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
        data_dir = "{}/db/data/user.db"

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
        data_dir = "{}/db/data/user.db"
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
