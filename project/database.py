import sqlite3
import os
from datetime import datetime

DATABASE_PATH = 'matricule_system.db'

def init_database():
    """Initialize the SQLite database with tables for allowed and scanned matricules."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create table for allowed matricules
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS allowed_matricules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricule TEXT UNIQUE NOT NULL,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
    ''')
    
    # Create table for scanned matricules
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scanned_matricules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricule TEXT NOT NULL,
            numbers TEXT,
            letters TEXT,
            scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_authorized INTEGER DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()

def add_allowed_matricule(matricule):
    """Add a matricule to the allowed list."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO allowed_matricules (matricule, status)
            VALUES (?, 'active')
        ''', (matricule,))
        conn.commit()
        print(f"Added allowed matricule: {matricule}")
        return True
    except sqlite3.IntegrityError:
        print(f"Matricule already exists: {matricule}")
        return False
    finally:
        conn.close()

def remove_allowed_matricule(matricule):
    """Remove a matricule from the allowed list."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE allowed_matricules SET status = ? WHERE matricule = ?', ('inactive', matricule))
    conn.commit()
    conn.close()

def get_allowed_matricules():
    """Get all active allowed matricules."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT matricule FROM allowed_matricules WHERE status = ?', ('active',))
    result = [row[0] for row in cursor.fetchall()]
    conn.close()
    return result

def add_scanned_matricule(matricule, numbers, letters, is_authorized):
    """Add a scanned matricule to the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scanned_matricules (matricule, numbers, letters, is_authorized)
        VALUES (?, ?, ?, ?)
    ''', (matricule, numbers, letters, 1 if is_authorized else 0))
    conn.commit()
    conn.close()

def get_scanned_history(limit=None):
    """Get the history of scanned matricules."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    if limit:
        cursor.execute('''
            SELECT matricule, numbers, letters, scan_timestamp, is_authorized
            FROM scanned_matricules
            ORDER BY scan_timestamp DESC
            LIMIT ?
        ''', (limit,))
    else:
        cursor.execute('''
            SELECT matricule, numbers, letters, scan_timestamp, is_authorized
            FROM scanned_matricules
            ORDER BY scan_timestamp DESC
        ''')
    result = []
    for row in cursor.fetchall():
        result.append({
            'matricule': row[0],
            'numbers': row[1],
            'letters': row[2],
            'timestamp': row[3],
            'is_authorized': bool(row[4])
        })
    conn.close()
    return result

def clear_scanned_history():
    """Clear all scanned matricules history."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM scanned_matricules')
    conn.commit()
    conn.close()

def get_database_stats():
    """Get statistics about the database."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM allowed_matricules WHERE status = ?', ('active',))
    allowed_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM scanned_matricules')
    scanned_count = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM scanned_matricules WHERE is_authorized = 1')
    authorized_scans = cursor.fetchone()[0]
    conn.close()
    return {
        'allowed_matricules': allowed_count,
        'total_scans': scanned_count,
        'authorized_scans': authorized_scans
    }

# Initialize database on import
if not os.path.exists(DATABASE_PATH):
    init_database()
