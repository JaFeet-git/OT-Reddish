import sqlite3
import datetime
import json
import os
import re

DB_FILE = "scans.db"
DEFAULT_VULN_TEXT_FILE = os.path.join(os.path.dirname(__file__), "vulnerability_catalog.txt")
ROCKWELL_DB_FILE = os.path.join(os.path.dirname(__file__), "plc_data.db")
ROCKWELL_CVE_TEXT_FILE = os.path.join(os.path.dirname(__file__), "CVE_List_2026_2025_2024.txt")

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
    # Prefer curated offline text feed when available.
    from_text = _load_rockwell_cves_from_text(limit=limit)
    if from_text:
        return from_text

    if os.path.exists(ROCKWELL_DB_FILE):
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
            return [
                {
                    "vendor": row[0],
                    "device_name": row[1],
                    "cve_id": row[2],
                    "severity": row[3]
                }
                for row in rows
            ]
        except sqlite3.Error:
            pass

    # Offline fallback: load curated CVE list from local text file.
    return _load_rockwell_cves_from_text(limit=limit)

def get_offline_cve_matches(catalog_matches, limit=6):
    if not catalog_matches:
        return []

    cve_rows = _load_all_cves_from_text()
    if not cve_rows:
        return []

    keywords = _build_cve_keywords(catalog_matches)
    if not keywords:
        return []

    vendor_hints = {
        "rockwell automation",
        "schneider electric",
        "siemens",
    }
    severity_rank = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
    scored = []

    for cve in cve_rows:
        vendor = str(cve.get("vendor", "")).lower()
        product = str(cve.get("device_name", "")).lower()
        haystack = f"{vendor} {product}"

        score = 0
        for kw in keywords:
            if kw in haystack:
                score += 1
        for hint in vendor_hints:
            if hint in keywords and hint in vendor:
                score += 3

        if score <= 0:
            continue

        scored.append(
            (
                score,
                severity_rank.get(str(cve.get("severity", "")).upper(), 0),
                str(cve.get("cve_id", "")),
                cve,
            )
        )

    scored.sort(key=lambda item: (item[0], item[1], item[2]), reverse=True)

    deduped = []
    seen_cves = set()
    for score, _sev_rank, _cve_id, cve in scored:
        cve_key = cve.get("cve_id")
        if not cve_key or cve_key in seen_cves:
            continue
        seen_cves.add(cve_key)
        enriched = dict(cve)
        enriched["score"] = score
        deduped.append(enriched)
        if len(deduped) >= limit:
            break

    return deduped

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

def wipe_scan_history():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM scan_history")
    deleted_rows = cursor.fetchone()[0]
    cursor.execute("DELETE FROM scan_history")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'scan_history'")
    conn.commit()
    conn.close()
    return deleted_rows

def _load_rockwell_cves_from_text(limit=5):
    if not os.path.exists(ROCKWELL_CVE_TEXT_FILE):
        return []

    preview = []
    with open(ROCKWELL_CVE_TEXT_FILE, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip().lstrip("\ufeff")
            if not line:
                continue

            parts = [part.strip() for part in line.split(",")]
            if parts and parts[0].lower() == "vendor":
                continue
            if not parts or parts[0].lower() != "rockwell automation":
                continue

            cve_index = next(
                (idx for idx, part in enumerate(parts) if re.match(r"^CVE-\d{4}-\d+$", part)),
                None
            )
            if cve_index is None or cve_index < 2:
                continue

            vendor = parts[0]
            device_name = ", ".join(parts[1:cve_index]).strip()
            cve_id = parts[cve_index]
            severity = parts[cve_index + 1] if cve_index + 1 < len(parts) else "UNKNOWN"

            preview.append(
                {
                    "vendor": vendor,
                    "device_name": device_name or "Unknown device",
                    "cve_id": cve_id,
                    "severity": severity,
                }
            )
            if len(preview) >= limit:
                break

    return preview

def _load_all_cves_from_text():
    if not os.path.exists(ROCKWELL_CVE_TEXT_FILE):
        return []

    rows = []
    with open(ROCKWELL_CVE_TEXT_FILE, "r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip().lstrip("\ufeff")
            if not line:
                continue

            parts = [part.strip() for part in line.split(",")]
            if parts and parts[0].lower() == "vendor":
                continue

            cve_index = next(
                (idx for idx, part in enumerate(parts) if re.match(r"^CVE-\d{4}-\d+$", part)),
                None
            )
            if cve_index is None or cve_index < 2:
                continue

            vendor = parts[0]
            device_name = ", ".join(parts[1:cve_index]).strip()
            cve_id = parts[cve_index]
            severity = parts[cve_index + 1] if cve_index + 1 < len(parts) else "UNKNOWN"
            attack_complexity = parts[cve_index + 2] if cve_index + 2 < len(parts) else "UNKNOWN"

            rows.append(
                {
                    "vendor": vendor,
                    "device_name": device_name or "Unknown device",
                    "cve_id": cve_id,
                    "severity": severity,
                    "attack_complexity": attack_complexity,
                }
            )

    return rows

def _build_cve_keywords(catalog_matches):
    stopwords = {
        "vector", "attack", "used", "port", "ports", "credential", "control",
        "tcp", "udp", "http", "https", "ftp", "ssh", "telnet", "n", "a"
    }
    words = set()

    for match in catalog_matches:
        combined = " ".join(
            [
                str(match.get("device_software", "")),
                str(match.get("protocol", "")),
                str(match.get("exploit", "")),
            ]
        ).lower()

        if "rockwell" in combined:
            words.add("rockwell automation")
        if "schneider" in combined:
            words.add("schneider electric")
        if "siemens" in combined:
            words.add("siemens")

        for token in re.findall(r"[a-z0-9][a-z0-9\-\+/]{2,}", combined):
            normalized = token.strip("-+/")
            if len(normalized) < 3:
                continue
            if normalized in stopwords:
                continue
            words.add(normalized)

    return words

def _decode_vulnerabilities(raw_value):
    if not raw_value:
        return []
    try:
        data = json.loads(raw_value)
        return data if isinstance(data, list) else []
    except json.JSONDecodeError:
        return []
