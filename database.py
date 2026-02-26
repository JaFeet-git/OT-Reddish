import sqlite3
import datetime
import os

DB_FILE = "scans.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scan_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            target_ip TEXT,
            scan_type TEXT,
            results TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_scan_log(target_ip, scan_type, results):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO scan_history (timestamp, target_ip, scan_type, results)
        VALUES (?, ?, ?, ?)
    ''', (timestamp, target_ip, scan_type, results))
    conn.commit()
    conn.close()

def get_all_logs():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, timestamp, target_ip, scan_type, results 
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
            "results": row[4]
        }
        for row in rows
    ]

def delete_log(log_id):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM scan_history WHERE id = ?', (log_id,))
    conn.commit()
    conn.close()
