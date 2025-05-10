"""
Database functionality for PowerPulse

This module handles database operations for storing battery history and settings.
"""

import os
import sqlite3
import datetime
from pathlib import Path

# Get application data directory
if os.name == 'nt':  # Windows
    APP_DATA_DIR = os.path.join(os.environ.get('APPDATA', ''), 'PowerPulse')
else:  # macOS and Linux
    APP_DATA_DIR = os.path.join(Path.home(), '.powerpulse')

# Ensure the directory exists
os.makedirs(APP_DATA_DIR, exist_ok=True)

# Database file path
DB_PATH = os.path.join(APP_DATA_DIR, 'battery_history.db')


def setup_database():
    """Set up the SQLite database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS battery_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        percentage REAL,
        is_charging INTEGER,
        power_plugged INTEGER,
        temperature REAL,
        remaining_time REAL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        level INTEGER,
        enabled INTEGER
    )
    ''')
    
    # Insert default notification settings if not present
    cursor.execute('SELECT COUNT(*) FROM notifications')
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
        INSERT INTO notifications (type, level, enabled)
        VALUES 
            ('low_battery', 20, 1),
            ('full_charge', 100, 1),
            ('custom_level', 80, 0)
        ''')
    
    # Create settings table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')
    
    # Insert default settings if not present
    default_settings = {
        'update_interval': '30',
        'start_on_boot': '0',
        'start_minimized': '0',
        'theme': 'clam',
    }
    
    cursor.execute('SELECT COUNT(*) FROM settings')
    if cursor.fetchone()[0] == 0:
        for key, value in default_settings.items():
            cursor.execute('INSERT INTO settings (key, value) VALUES (?, ?)', (key, value))
    
    conn.commit()
    conn.close()


def save_battery_info(battery_info):
    """Save battery information to the database"""
    if not battery_info:
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO battery_history 
    (timestamp, percentage, is_charging, power_plugged, temperature, remaining_time)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        datetime.datetime.now().isoformat(),
        battery_info['percentage'],
        int(battery_info['is_charging']),
        int(battery_info['power_plugged']),
        battery_info['temperature'],
        battery_info['remaining_time']
    ))
    
    conn.commit()
    conn.close()
    return True


def get_battery_history(days=7):
    """Get battery history for the specified number of days"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Calculate the date threshold
    date_threshold = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
    
    cursor.execute('''
    SELECT timestamp, percentage, is_charging, power_plugged, temperature, remaining_time
    FROM battery_history
    WHERE timestamp >= ?
    ORDER BY timestamp
    ''', (date_threshold,))
    
    history = cursor.fetchall()
    conn.close()
    
    return history


def get_notification_settings():
    """Get notification settings from the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT type, level, enabled FROM notifications')
    settings = cursor.fetchall()
    
    conn.close()
    
    return settings


def update_notification_setting(notification_type, level=None, enabled=None):
    """Update a notification setting"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if level is not None:
        cursor.execute('''
        UPDATE notifications 
        SET level = ? 
        WHERE type = ?
        ''', (level, notification_type))
    
    if enabled is not None:
        cursor.execute('''
        UPDATE notifications 
        SET enabled = ? 
        WHERE type = ?
        ''', (1 if enabled else 0, notification_type))
    
    conn.commit()
    conn.close()


def get_setting(key, default=None):
    """Get a setting value from the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return result[0]
    return default


def update_setting(key, value):
    """Update a setting value in the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT OR REPLACE INTO settings (key, value)
    VALUES (?, ?)
    ''', (key, str(value)))
    
    conn.commit()
    conn.close()


def clear_old_history(days_to_keep=30):
    """Remove battery history older than specified days"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Calculate the date threshold
    date_threshold = (datetime.datetime.now() - datetime.timedelta(days=days_to_keep)).isoformat()
    
    cursor.execute('''
    DELETE FROM battery_history
    WHERE timestamp < ?
    ''', (date_threshold,))
    
    deleted_rows = cursor.rowcount
    conn.commit()
    conn.close()
    
    return deleted_rows
