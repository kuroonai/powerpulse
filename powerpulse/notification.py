"""
Notification functionality for PowerPulse

This module handles system notifications for battery events.
"""

import sys
import subprocess
from powerpulse.database import get_notification_settings


def check_notifications(battery_info):
    """Check if any notification thresholds have been met"""
    if not battery_info:
        return
    
    # Get notification settings
    notifications = get_notification_settings()
    
    for notification_type, level, enabled in notifications:
        if not enabled:
            continue
            
        if notification_type == 'low_battery' and battery_info['percentage'] <= level and not battery_info['power_plugged']:
            send_notification(f"Low Battery Alert", f"Battery at {battery_info['percentage']}%, please connect charger")
        
        elif notification_type == 'full_charge' and battery_info['percentage'] >= level and battery_info['power_plugged']:
            send_notification(f"Battery Fully Charged", f"Battery reached {battery_info['percentage']}%, you can disconnect charger")
        
        elif notification_type == 'custom_level' and battery_info['percentage'] >= level and battery_info['is_charging']:
            send_notification(f"Battery Level Reached", f"Battery reached {battery_info['percentage']}%")


def send_notification(title, message):
    """Send system notification based on platform"""
    print(f"{title}: {message}")  # Always print to console
    
    try:
        if sys.platform == 'win32':
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast(title, message, duration=10, threaded=True)
                return True
            except ImportError:
                # Fallback for Windows
                try:
                    import ctypes
                    MessageBox = ctypes.windll.user32.MessageBoxW
                    MessageBox(None, message, title, 0)
                    return True
                except:
                    pass
        
        elif sys.platform == 'darwin':  # macOS
            apple_script = f'display notification "{message}" with title "{title}"'
            subprocess.call(['osascript', '-e', apple_script])
            return True
        
        elif sys.platform == 'linux':
            # Try different notification methods
            try:
                subprocess.call(['notify-send', title, message])
                return True
            except FileNotFoundError:
                try:
                    subprocess.call(['zenity', '--notification', '--text', f"{title}: {message}"])
                    return True
                except FileNotFoundError:
                    pass
    
    except Exception as e:
        print(f"Failed to send notification: {e}")
    
    return False
