"""
Utility functions for PowerPulse

This module provides common utility functions used across the application.
"""

import os
import sys
import platform
import subprocess


def get_platform_info():
    """Get detailed information about the current platform"""
    info = {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': platform.python_version(),
    }
    
    # Add platform-specific information
    if platform.system() == 'Windows':
        info['windows_edition'] = platform.win32_edition()
    elif platform.system() == 'Darwin':  # macOS
        info['mac_version'] = platform.mac_ver()[0]
    elif platform.system() == 'Linux':
        try:
            # Try to get distribution information
            import distro
            info['distro'] = distro.name()
            info['distro_version'] = distro.version()
        except ImportError:
            try:
                with open('/etc/os-release', 'r') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith('PRETTY_NAME='):
                            info['distro'] = line.split('=')[1].strip().strip('"')
                            break
            except:
                info['distro'] = 'Unknown'
    
    return info


def format_time_remaining(seconds):
    """Format time remaining in a human-readable format"""
    if seconds is None or seconds <= 0:
        return "Unknown"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"


def is_admin():
    """Check if the application is running with administrator/root privileges"""
    try:
        if sys.platform == 'win32':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:  # Unix-based systems
            return os.geteuid() == 0
    except:
        return False


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_path, 'resources', relative_path)
    except:
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', relative_path)


def open_file_explorer(path):
    """Open the file explorer at the specified path"""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    
    if sys.platform == 'win32':
        os.startfile(path)
    elif sys.platform == 'darwin':  # macOS
        subprocess.call(['open', path])
    else:  # Linux
        subprocess.call(['xdg-open', path])


def create_shortcut(target_path, shortcut_path, description="PowerPulse Battery Monitor"):
    """Create a shortcut/link to the application"""
    try:
        if sys.platform == 'win32':
            import winshell
            from win32com.client import Dispatch
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = target_path
            shortcut.Description = description
            shortcut.IconLocation = target_path
            shortcut.save()
            return True
        
        elif sys.platform == 'darwin':  # macOS
            # Create a symbolic link
            subprocess.call(['ln', '-sf', target_path, shortcut_path])
            return True
        
        else:  # Linux
            # Create a .desktop file
            desktop_content = f"""[Desktop Entry]
Type=Application
Name=PowerPulse
Exec={target_path}
Icon={os.path.join(os.path.dirname(target_path), 'resources', 'powerpulse.png')}
Comment={description}
Terminal=false
Categories=Utility;System;
"""
            os.makedirs(os.path.dirname(shortcut_path), exist_ok=True)
            with open(shortcut_path, 'w') as f:
                f.write(desktop_content)
            os.chmod(shortcut_path, 0o755)
            return True
    
    except Exception as e:
        print(f"Error creating shortcut: {e}")
        return False
