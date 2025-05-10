"""
Battery information functionality for PowerPulse
"""

import os
import sys
import subprocess

# Cross-platform battery info
if sys.platform == 'win32':
    import psutil
elif sys.platform == 'darwin':  # macOS
    pass  # Import handled at function level
elif sys.platform == 'linux':
    pass  # Import handled at function level
else:
    print(f"Unsupported platform: {sys.platform}")
    sys.exit(1)


def get_battery_info():
    """Get current battery information based on platform"""
    if sys.platform == 'win32':
        return get_battery_info_windows()
    elif sys.platform == 'darwin':
        return get_battery_info_macos()
    elif sys.platform == 'linux':
        return get_battery_info_linux()
    return None


def get_battery_info_windows():
    """Get battery information on Windows using psutil"""
    try:
        battery = psutil.sensors_battery()
        if battery:
            return {
                'percentage': battery.percent,
                'is_charging': battery.power_plugged and battery.percent < 100,
                'power_plugged': battery.power_plugged,
                'temperature': None,  # Not directly available via psutil
                'remaining_time': battery.secsleft if battery.secsleft != -1 else None
            }
    except Exception as e:
        print(f"Error getting battery info: {e}")
    return None


def get_battery_info_macos():
    """Get battery information on macOS using system commands"""
    try:
        output = subprocess.check_output(['pmset', '-g', 'batt'], text=True)
        percentage = float(output.split('%')[0].split('\t')[-1].strip())
        charging_status = 'charging' in output.lower()
        plugged = 'ac' in output.lower()
