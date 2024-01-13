import xml.etree.ElementTree as ET
import sqlite3
from terminal.data import TerminalData
import os


class NmapToSqlite:
    def __init__(self, db_name):
        data_dir = "{}/db/data/projects/{}/".format(TerminalData.root_dir, TerminalData.current_project)
        self.db_file = "{}{}.db".format(data_dir, db_name)

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