import sqlite3
import datetime
import json
import os

DB_FILE = "scans.db"
DEFAULT_VULN_TEXT_FILE = os.path.join(os.path.dirname(__file__), "vulnerability_catalog.txt")
ROCKWELL_DB_FILE = "/Users/issac/Downloads/plc_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            target_ip TEXT,
            scan_type TEXT,
            results TEXT,
            vulnerabilities TEXT DEFAULT '[]'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vulnerability_catalog (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_software TEXT NOT NULL,
            protocol TEXT NOT NULL,
            port INTEGER NOT NULL,
            exploit TEXT NOT NULL
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_vuln_catalog_port ON vulnerability_catalog(port)')

    # Lightweight migration for existing scan_history tables.
    cursor.execute("PRAGMA table_info(scan_history)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    if "vulnerabilities" not in existing_columns:
        cursor.execute("ALTER TABLE scan_history ADD COLUMN vulnerabilities TEXT DEFAULT '[]'")

    # Seed catalog from bundled text format if table is empty.
    cursor.execute("SELECT COUNT(*) FROM vulnerability_catalog")
    if cursor.fetchone()[0] == 0:
        try:
            load_vulnerability_catalog_from_text(DEFAULT_VULN_TEXT_FILE, replace=True, conn=conn)
        except FileNotFoundError:
            # Optional seed file; app still works without it.
            pass

    conn.commit()
    conn.close()

def add_scan_log(target_ip, scan_type, results, vulnerabilities=None):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    vulnerabilities_json = json.dumps(vulnerabilities or [])
    cursor.execute('''
        INSERT INTO scan_history (timestamp, target_ip, scan_type, results, vulnerabilities)
        VALUES (?, ?, ?, ?, ?)
    ''', (timestamp, target_ip, scan_type, results, vulnerabilities_json))
    conn.commit()
    conn.close()

def get_all_logs():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, timestamp, target_ip, scan_type, results, vulnerabilities
        FROM scan_history 
        ORDER BY id DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    # Return as list of dictionaries for easier use
    return [
        {
            "id": row[0],
            "timestamp": row[1],
            "target_ip": row[2],
            "scan_type": row[3],
            "results": row[4],
            "vulnerabilities": _decode_vulnerabilities(row[5])
        }
        for row in rows
    ]

def get_vulnerability_matches_by_ports(ports):
    if not ports:
        return []
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    placeholders = ",".join(["?"] * len(ports))
    cursor.execute(
        f'''
        SELECT device_software, protocol, port, exploit
        FROM vulnerability_catalog
        WHERE port IN ({placeholders})
        ORDER BY port ASC, device_software ASC
        ''',
        tuple(ports)
    )
    rows = cursor.fetchall()
    conn.close()
    return [
        {
            "device_software": row[0],
            "protocol": row[1],
            "port": row[2],
            "exploit": row[3]
        }
        for row in rows
    ]

def get_rockwell_cves_preview(limit=5):
    if not os.path.exists(ROCKWELL_DB_FILE):
        return []

    try:
        conn = sqlite3.connect(ROCKWELL_DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            '''
            SELECT vendor, device_name, cve_id, severity
            FROM rockwell_cves
            WHERE cve_id IS NOT NULL AND TRIM(cve_id) != ''
            LIMIT ?
            ''',
            (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
    except sqlite3.Error:
        return []

    return [
        {
            "vendor": row[0],
            "device_name": row[1],
            "cve_id": row[2],
            "severity": row[3]
        }
        for row in rows
    ]

def load_vulnerability_catalog_from_text(file_path, replace=True, conn=None):
    owns_conn = conn is None
    if owns_conn:
        conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    parsed_entries = []
    with open(file_path, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            # Header example: device/software, protocol, port, exploit
            if line.lower().startswith("device/software"):
                continue
            parts = [part.strip() for part in line.split(",", 3)]
            if len(parts) != 4:
                continue
            device_software, protocol, port_text, exploit = parts
            try:
                port = int(port_text)
            except ValueError:
                continue
            parsed_entries.append((device_software, protocol, port, exploit))

    if replace:
        cursor.execute("DELETE FROM vulnerability_catalog")
    if parsed_entries:
        cursor.executemany(
            '''
            INSERT INTO vulnerability_catalog (device_software, protocol, port, exploit)
            VALUES (?, ?, ?, ?)
            ''',
            parsed_entries
        )

    if owns_conn:
        conn.commit()
        conn.close()
    return len(parsed_entries)

def delete_log(log_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM scan_history WHERE id = ?', (log_id,))
    conn.commit()
    conn.close()

def _decode_vulnerabilities(raw_value):
    if not raw_value:
        return []
    try:
        data = json.loads(raw_value)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []
