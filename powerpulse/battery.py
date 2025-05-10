"""
Battery information functionality for PowerPulse

This module provides cross-platform functions to retrieve battery information
from Windows, macOS, and Linux systems.
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


def get_battery_info_linux():
    """Get battery information on Linux using system commands"""
    try:
        # Try using upower for more detailed info
        battery_path = None
        try:
            devices = subprocess.check_output(['upower', '--enumerate'], text=True).strip().split('\n')
            for device in devices:
                if 'battery' in device.lower():
                    battery_path = device
                    break
            
            if battery_path:
                info = subprocess.check_output(['upower', '--show-info', battery_path], text=True)
                
                percentage = None
                percentage_line = [l for l in info.split('\n') if 'percentage' in l.lower()]
                if percentage_line:
                    percentage = float(percentage_line[0].split(':')[1].strip().rstrip('%'))
                
                state = None
                state_line = [l for l in info.split('\n') if 'state' in l.lower()]
                if state_line:
                    state = state_line[0].split(':')[1].strip()
                
                is_charging = state == 'charging'
                power_plugged = state in ('charging', 'fully-charged')
                
                temp = None
                temp_line = [l for l in info.split('\n') if 'temperature' in l.lower()]
                if temp_line:
                    temp = float(temp_line[0].split(':')[1].strip().split(' ')[0])
                
                time_remaining = None
                time_line = [l for l in info.split('\n') if 'time to empty' in l.lower()]
                if time_line and not is_charging:
                    time_str = time_line[0].split(':')[1].strip()
                    if 'hours' in time_str and 'minutes' in time_str:
                        hours = float(time_str.split('hours')[0].strip())
                        minutes = float(time_str.split('hours')[1].split('minutes')[0].strip())
                        time_remaining = hours * 3600 + minutes * 60
                
                return {
                    'percentage': percentage,
                    'is_charging': is_charging,
                    'power_plugged': power_plugged,
                    'temperature': temp,
                    'remaining_time': time_remaining
                }
        except Exception:
            # Fallback to /sys/class/power_supply/
            path = '/sys/class/power_supply/BAT0'
            if not os.path.exists(path):
                path = '/sys/class/power_supply/BAT1'
                if not os.path.exists(path):
                    return None
            
            with open(f"{path}/capacity", 'r') as f:
                percentage = float(f.read().strip())
            
            with open(f"{path}/status", 'r') as f:
                status = f.read().strip()
            
            is_charging = status.lower() == 'charging'
            power_plugged = status.lower() in ('charging', 'full')
            
            # Temperature might be in different locations
            temp = None
            temp_path = f"{path}/temp"
            if os.path.exists(temp_path):
                with open(temp_path, 'r') as f:
                    temp = float(f.read().strip()) / 10.0  # Usually in tenths of degrees
            
            return {
                'percentage': percentage,
                'is_charging': is_charging,
                'power_plugged': power_plugged,
                'temperature': temp,
                'remaining_time': None  # Would need additional calculation
            }
    except Exception as e:
        print(f"Error getting battery info: {e}")
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
        plugged = 'ac' in output.lower() or charging_status
        
        # Get more detailed info with system_profiler
        detailed = subprocess.check_output(['system_profiler', 'SPPowerDataType'], text=True)
        
        # Extract temperature (not always available)
        temp = None
        temp_line = [l for l in detailed.split('\n') if 'Temperature' in l]
        if temp_line:
            temp = float(temp_line[0].split(':')[1].strip().split(' ')[0])
        
        # Extract time remaining
        time_remaining = None
        if 'estimate' in output.lower() and not charging_status:
            time_str = output.split(';')[1].strip()
            if ':' in time_str:
                hours, minutes = map(int, time_str.split(':'))
                time_remaining = hours * 3600 + minutes * 60
        
        return {
            'percentage': percentage,
            'is_charging': charging_status,
            'power_plugged': plugged,
            'temperature': temp,
            'remaining_time': time_remaining
        }
