import xml.etree.ElementTree as ET
import sqlite3
from terminal.data import TerminalData

class NmapToSqlite:
    def __init__(self):
        self.data_dir = "{}/db/data/".format(TerminalData.root_dir)

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

