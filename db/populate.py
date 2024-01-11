import xml.etree.ElementTree as ET
import sqlite3
from terminal.data import TerminalData

class NmapToSqlite:
    def __init__(self, db_name):
        data_dir = "{}/db/data/".format(TerminalData.root_dir)
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
                version TEXT
            )
        ''')

        for host_data in self.results:
            for port_data in host_data['ports']:
                cursor.execute("INSERT OR REPLACE INTO hosts (ip, port, service_name, version) VALUES (?, ?, ?, ?)",
                               (host_data['ip'], port_data['port'], port_data['service'], port_data['version']))

        conn.commit()
        conn.close()

