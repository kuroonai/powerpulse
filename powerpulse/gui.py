"""
GUI functionality for PowerPulse

This module implements the graphical user interface for the application.
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from powerpulse.battery import get_battery_info
from powerpulse.database import (
    setup_database, save_battery_info, get_notification_settings,
    update_notification_setting, get_setting, update_setting
)
from powerpulse.stats import calculate_statistics, generate_history_plot, generate_daily_usage_plot
from powerpulse.notifications import check_notifications


class PowerPulseGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PowerPulse Battery Monitor")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # Set app icon
        self.set_app_icon()
        
        # Initialize database
        setup_database()
        
        # Create style
        self.style = ttk.Style()
        theme = get_setting('theme', 'clam')
        if theme in self.style.theme_names():
            self.style.theme_use(theme)
        
        # Variables
        self.current_percentage = tk.StringVar(value="--")
        self.current_status = tk.StringVar(value="Unknown")
        self.current_time = tk.StringVar(value="--")
        self.update_interval = tk.IntVar(value=int(get_setting('update_interval', '30')))
        self.monitoring_active = False
        self.monitoring_thread = None
        self.update_gui_job = None
        
        # Create tabs
        self.tab_control = ttk.Notebook(self.root)
        
        self.tab_monitor = ttk.Frame(self.tab_control)
        self.tab_history = ttk.Frame(self.tab_control)
        self.tab_stats = ttk.Frame(self.tab_control)
        self.tab_settings = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.tab_monitor, text="Monitor")
        self.tab_control.add(self.tab_history, text="History")
        self.tab_control.add(self.tab_stats, text="Statistics")
        self.tab_control.add(self.tab_settings, text="Settings")
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Set up each tab
        self.setup_monitor_tab()
        self.setup_history_tab()
        self.setup_stats_tab()
        self.setup_settings_tab()
        
        # Set up system tray icon if available
        self.setup_tray_icon()
        
        # Initial battery check
        self.update_battery_info()
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def set_app_icon(self):
        """Set the application icon"""
        try:
            # Look for the icon in several possible locations
            icon_paths = [
                os.path.join(os.path.dirname(__file__), "resources", "powerpulse.ico"),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), "resources", "powerpulse.ico"),
            ]
            
            for icon_path in icon_paths:
                if os.path.exists(icon_path):
                    if sys.platform == 'win32':
                        self.root.iconbitmap(icon_path)
                    elif sys.platform in ('linux', 'darwin'):
                        # For Linux and macOS, use a different approach
                        img = tk.PhotoImage(file=icon_path.replace('.ico', '.png'))
                        self.root.tk.call('wm', 'iconphoto', self.root._w, img)
                    break
        except Exception as e:
            print(f"Could not set application icon: {e}")
    
    def setup_tray_icon(self):
        """Set up system tray icon if available"""
        self.tray_icon = None
        
        # Windows-specific tray icon
        if sys.platform == 'win32':
            try:
                from pystray import Icon, Menu, MenuItem
                from PIL import Image, ImageDraw
                
                # Create an icon image
                icon_image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
                draw = ImageDraw.Draw(icon_image)
                draw.ellipse((4, 4, 60, 60), fill=(0, 120, 212))
                draw.rectangle((28, 14, 36, 50), fill='white')
                
                # Define tray icon menu
                menu = Menu(
                    MenuItem('Show', self.show_window),
                    MenuItem('Start Monitoring', self.start_monitoring),
                    MenuItem('Stop Monitoring', self.stop_monitoring),
                    MenuItem('Exit', self.exit_app)
                )
                
                # Create the tray icon
                self.tray_icon = Icon('PowerPulse', icon_image, 'PowerPulse', menu)
                
                # Start the icon in a separate thread
                threading.Thread(target=self.tray_icon.run, daemon=True).start()
            except ImportError:
                print("pystray package not installed. System tray functionality disabled.")
    
    def show_window(self, icon=None, item=None):
        """Show the main window"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
    
    def start_monitoring(self, icon=None, item=None):
        """Start monitoring from tray icon"""
        if not self.monitoring_active:
            self.toggle_monitoring()
    
    def stop_monitoring(self, icon=None, item=None):
        """Stop monitoring from tray icon"""
        if self.monitoring_active:
            self.toggle_monitoring()
    
    def exit_app(self, icon=None, item=None):
        """Exit the application from tray icon"""
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
    
    def on_close(self):
        """Handle window close event"""
        start_minimized = bool(int(get_setting('start_minimized', '0')))
        
        if start_minimized and self.tray_icon:
            # Minimize to tray
            self.root.withdraw()
        else:
            # Exit application
            self.exit_app()
    
    def setup_monitor_tab(self):
        """Set up the Monitor tab"""
        frame = ttk.Frame(self.tab_monitor, padding="20")
        frame.pack(fill="both", expand=True)
        
        # Battery level display
        ttk.Label(frame, text="Current Battery Status", font=("Arial", 16, "bold")).pack(pady=(0, 20))
        
        # Battery percentage in large font
        ttk.Label(frame, textvariable=self.current_percentage, font=("Arial", 48, "bold")).pack()
        
        # Battery status
        ttk.Label(frame, textvariable=self.current_status, font=("Arial", 14)).pack(pady=(0, 10))
        
        # Remaining time
        ttk.Label(frame, textvariable=self.current_time, font=("Arial", 12)).pack(pady=(0, 20))
        
        # Monitoring controls
        control_frame = ttk.Frame(frame)
        control_frame.pack(pady=20)
        
        ttk.Label(control_frame, text="Update interval:").grid(row=0, column=0, padx=5)
        ttk.Spinbox(control_frame, from_=5, to=300, width=5, textvariable=self.update_interval).grid(row=0, column=1, padx=5)
        ttk.Label(control_frame, text="seconds").grid(row=0, column=2, padx=5)
        
        self.monitor_button = ttk.Button(control_frame, text="Start Monitoring", command=self.toggle_monitoring)
        self.monitor_button.grid(row=0, column=3, padx=20)
        
        # Manual update button
        ttk.Button(frame, text="Update Now", command=self.update_battery_info).pack(pady=10)
    
    def setup_history_tab(self):
        """Set up the History tab"""
        frame = ttk.Frame(self.tab_history, padding="20")
        frame.pack(fill="both", expand=True)
        
        # Controls for history view
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(control_frame, text="Show data for past:").pack(side="left", padx=5)
        
        self.history_days = tk.IntVar(value=7)
        days_options = [1, 3, 7, 14, 30]
        
        for days in days_options:
            rb = ttk.Radiobutton(control_frame, text=f"{days} {'day' if days == 1 else 'days'}", 
                                variable=self.history_days, value=days, command=self.update_history_plot)
            rb.pack(side="left", padx=10)
        
        # Create a notebook for different history views
        history_notebook = ttk.Notebook(frame)
        history_notebook.pack(fill="both", expand=True, pady=10)
        
        # Tab for battery percentage history
        self.history_plot_frame = ttk.Frame(history_notebook)
        history_notebook.add(self.history_plot_frame, text="Battery Level")
        
        # Tab for daily usage
        self.daily_usage_frame = ttk.Frame(history_notebook)
        history_notebook.add(self.daily_usage_frame, text="Daily Usage")
        
        # Initial plots
        self.update_history_plot()
        self.update_daily_usage_plot()
    
    def setup_stats_tab(self):
        """Set up the Statistics tab"""
        frame = ttk.Frame(self.tab_stats, padding="20")
        frame.pack(fill="both", expand=True)
        
        # Controls for stats view
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(control_frame, text="Calculate statistics for past:").pack(side="left", padx=5)
        
        self.stats_days = tk.IntVar(value=7)
        days_options = [1, 3, 7, 14, 30]
        
        for days in days_options:
            rb = ttk.Radiobutton(control_frame, text=f"{days} {'day' if days == 1 else 'days'}", 
                                variable=self.stats_days, value=days, command=self.update_statistics)
            rb.pack(side="left", padx=10)
        
        # Statistics display
        self.stats_frame = ttk.Frame(frame)
        self.stats_frame.pack(fill="both", expand=True, pady=10)
        
        # Initial stats
        self.update_statistics()
    
    def setup_settings_tab(self):
        """Set up the Settings tab"""
        frame = ttk.Frame(self.tab_settings, padding="20")
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="Notification Settings", font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 10))
        
        # Get current notification settings
        notifications = get_notification_settings()
        
        # Set up notification settings UI
        self.notification_vars = {}
        
        for i, (notification_type, level, enabled) in enumerate(notifications):
            frame_row = ttk.Frame(frame)
            frame_row.pack(fill="x", pady=5)
            
            # Format the notification type name
            friendly_name = notification_type.replace('_', ' ').title()
            
            # Enabled/disabled checkbox
            enabled_var = tk.BooleanVar(value=bool(enabled))
            self.notification_vars[f"{notification_type}_enabled"] = enabled_var
            enabled_cb = ttk.Checkbutton(frame_row, text=friendly_name, variable=enabled_var)
            enabled_cb.pack(side="left", padx=(0, 10))
            
            # Level spinbox
            ttk.Label(frame_row, text="Trigger at:").pack(side="left", padx=5)
            level_var = tk.IntVar(value=level)
            self.notification_vars[f"{notification_type}_level"] = level_var
            ttk.Spinbox(frame_row, from_=1, to=100, width=5, textvariable=level_var).pack(side="left", padx=5)
            ttk.Label(frame_row, text="%").pack(side="left")
        
        # Save button
        ttk.Button(frame, text="Save Notification Settings", command=self.save_notification_settings).pack(anchor="w", pady=20)
        
        # Application settings
        ttk.Separator(frame, orient="horizontal").pack(fill="x", pady=20)
        ttk.Label(frame, text="Application Settings", font=("Arial", 14, "bold")).pack(anchor="w", pady=(0, 10))
        
        # Start on system boot option
        self.start_on_boot = tk.BooleanVar(value=bool(int(get_setting('start_on_boot', '0'))))
        ttk.Checkbutton(frame, text="Start PowerPulse on system boot", variable=self.start_on_boot, 
                      command=self.toggle_autostart).pack(anchor="w", pady=5)
        
        # Start minimized option
        self.start_minimized = tk.BooleanVar(value=bool(int(get_setting('start_minimized', '0'))))
        ttk.Checkbutton(frame, text="Start minimized to system tray", variable=self.start_minimized,
                      command=lambda: update_setting('start_minimized', int(self.start_minimized.get()))).pack(anchor="w", pady=5)
        
        # Theme selection
        theme_frame = ttk.Frame(frame)
        theme_frame.pack(fill="x", pady=5, anchor="w")
        
        ttk.Label(theme_frame, text="UI Theme:").pack(side="left", padx=(0, 10))
        
        themes = self.style.theme_names()
        self.selected_theme = tk.StringVar(value=self.style.theme_use())
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.selected_theme, values=themes, state="readonly", width=15)
        theme_combo.pack(side="left")
        theme_combo.bind("<<ComboboxSelected>>", self.change_theme)
    
    def toggle_autostart(self):
        """Configure application to start on system boot"""
        autostart = self.start_on_boot.get()
        update_setting('start_on_boot', int(autostart))
        
        if sys.platform == 'win32':
            import winreg
            
            key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
            
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE) as key:
                    if autostart:
                        executable = sys.executable
                        script_path = os.path.abspath(sys.argv[0])
                        winreg.SetValueEx(key, "PowerPulse", 0, winreg.REG_SZ, f'"{executable}" "{script_path}" --gui')
                    else:
                        try:
                            winreg.DeleteValue(key, "PowerPulse")
                        except FileNotFoundError:
                            pass
            except Exception as e:
                messagebox.showerror("Error", f"Failed to configure autostart: {e}")
        
        elif sys.platform == 'darwin':  # macOS
            plist_path = os.path.expanduser("~/Library/LaunchAgents/com.powerpulse.app.plist")
            
            if autostart:
                # Create a launchd plist file
                executable = sys.executable
                script_path = os.path.abspath(sys.argv[0])
                
                plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.powerpulse.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>{executable}</string>
        <string>{script_path}</string>
        <string>--gui</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
'''
                os.makedirs(os.path.dirname(plist_path), exist_ok=True)
                
                try:
                    with open(plist_path, 'w') as f:
                        f.write(plist_content)
                    # Load the agent
                    subprocess.call(['launchctl', 'load', plist_path])
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to configure autostart: {e}")
            else:
                # Remove the launchd plist file
                try:
                    if os.path.exists(plist_path):
                        # Unload the agent
                        subprocess.call(['launchctl', 'unload', plist_path])
                        os.remove(plist_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to remove autostart: {e}")
        
        elif sys.platform == 'linux':
            autostart_dir = os.path.expanduser("~/.config/autostart")
            desktop_file = os.path.join(autostart_dir, "powerpulse.desktop")
            
            if autostart:
                # Create a .desktop file for autostart
                executable = sys.executable
                script_path = os.path.abspath(sys.argv[0])
                
                desktop_content = f'''[Desktop Entry]
Type=Application
Name=PowerPulse
Exec={executable} {script_path} --gui
Terminal=false
Hidden=false
X-GNOME-Autostart-enabled=true
'''
                os.makedirs(autostart_dir, exist_ok=True)
                
                try:
                    with open(desktop_file, 'w') as f:
                        f.write(desktop_content)
                    os.chmod(desktop_file, 0o755)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to configure autostart: {e}")
            else:
                # Remove the .desktop file
                try:
                    if os.path.exists(desktop_file):
                        os.remove(desktop_file)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to remove autostart: {e}")
    
    def change_theme(self, event=None):
        """Change the application theme"""
        theme = self.selected_theme.get()
        self.style.theme_use(theme)
        update_setting('theme', theme)
    
    def save_notification_settings(self):
        """Save notification settings to database"""
        # Get current notification types
        notifications = get_notification_settings()
        notification_types = [row[0] for row in notifications]
        
        # Update each notification setting
        for notification_type in notification_types:
            enabled = int(self.notification_vars[f"{notification_type}_enabled"].get())
            level = self.notification_vars[f"{notification_type}_level"].get()
            
            update_notification_setting(notification_type, level, enabled)
        
        messagebox.showinfo("Settings Saved", "Notification settings have been saved.")
    
    def toggle_monitoring(self):
        """Start or stop continuous battery monitoring"""
        if self.monitoring_active:
            # Stop monitoring
            self.monitoring_active = False
            self.monitor_button.config(text="Start Monitoring")
            
            if self.update_gui_job:
                self.root.after_cancel(self.update_gui_job)
                self.update_gui_job = None
        else:
            # Start monitoring
            self.monitoring_active = True
            self.monitor_button.config(text="Stop Monitoring")
            
            # Update interval setting
            update_setting('update_interval', self.update_interval.get())
            
            # Start the monitoring thread
            if not self.monitoring_thread or not self.monitoring_thread.is_alive():
                self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
                self.monitoring_thread.start()
            
            # Schedule regular GUI updates
            self.update_gui()
    
    def monitoring_loop(self):
        """Background thread for battery monitoring"""
        while self.monitoring_active:
            # Save battery info to database
            info = get_battery_info()
            if info:
                save_battery_info(info)
                check_notifications(info)
            
            # Sleep for the specified interval
            time.sleep(self.update_interval.get())
    
    def update_gui(self):
        """Update the GUI with latest battery information"""
        if self.monitoring_active:
            self.update_battery_info()
            self.update_gui_job = self.root.after(self.update_interval.get() * 1000, self.update_gui)
    
    def update_battery_info(self):
        """Update the current battery information display"""
        info = get_battery_info()
        
        if not info:
            self.current_percentage.set("--")
            self.current_status.set("Error: Could not retrieve battery information")
            self.current_time.set("")
            return
        
        # Save to database if monitoring is active
        if self.monitoring_active:
            save_battery_info(info)
            check_notifications(info)
        
        # Update display
        self.current_percentage.set(f"{int(info['percentage'])}%")
        
        if info['is_charging']:
            self.current_status.set("Status: Charging")
        else:
            self.current_status.set("Status: Discharging")
        
        # Display remaining time if available
        if info['remaining_time'] and info['remaining_time'] > 0:
            hours = int(info['remaining_time'] / 3600)
            minutes = int((info['remaining_time'] % 3600) / 60)
            
            if info['is_charging']:
                self.current_time.set(f"Estimated time to full: {hours}h {minutes}m")
            else:
                self.current_time.set(f"Estimated remaining time: {hours}h {minutes}m")
        else:
            self.current_time.set("")
        
        return True
    
    def update_history_plot(self):
        """Update the battery history plot"""
        # Clear the existing plot frame
        for widget in self.history_plot_frame.winfo_children():
            widget.destroy()
        
        # Generate a new plot
        days = self.history_days.get()
        fig = generate_history_plot(days)
        
        if fig:
            canvas = FigureCanvasTkAgg(fig, self.history_plot_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            label = ttk.Label(self.history_plot_frame, text=f"No data available for the last {days} days")
            label.pack(pady=50)
    
    def update_daily_usage_plot(self):
        """Update the daily usage plot"""
        # Clear the existing plot frame
        for widget in self.daily_usage_frame.winfo_children():
            widget.destroy()
        
        # Generate a new plot
        days = self.history_days.get()
        fig = generate_daily_usage_plot(days)
        
        if fig:
            canvas = FigureCanvasTkAgg(fig, self.daily_usage_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
        else:
            label = ttk.Label(self.daily_usage_frame, text=f"No data available for the last {days} days")
            label.pack(pady=50)
    
    def update_statistics(self):
        """Update the statistics display"""
        # Clear the existing stats frame
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        
        # Calculate new statistics
        days = self.stats_days.get()
        stats = calculate_statistics(days)
        
        # Display statistics in a grid
        row = 0
        stat_frame = ttk.Frame(self.stats_frame)
        stat_frame.pack(pady=20)
        
        # Create a heading
        ttk.Label(stat_frame, text=f"Battery Statistics (Last {days} days)", 
                font=("Arial", 14, "bold")).grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 10))
        row += 1
        
        # Add each statistic
        if stats['average_discharge_rate'] is not None:
            ttk.Label(stat_frame, text="Average Discharge Rate:").grid(row=row, column=0, sticky="w", padx=(0, 10), pady=5)
            ttk.Label(stat_frame, text=f"{stats['average_discharge_rate']:.2f}% per hour").grid(row=row, column=1, sticky="w")
            row += 1
        
        if stats['average_charge_rate'] is not None:
            ttk.Label(stat_frame, text="Average Charge Rate:").grid(row=row, column=0, sticky="w", padx=(0, 10), pady=5)
            ttk.Label(stat_frame, text=f"{stats['average_charge_rate']:.2f}% per hour").grid(row=row, column=1, sticky="w")
            row += 1
        
        ttk.Label(stat_frame, text="Discharge/Charge Cycles:").grid(row=row, column=0, sticky="w", padx=(0, 10), pady=5)
        ttk.Label(stat_frame, text=f"{stats['discharge_cycles']}").grid(row=row, column=1, sticky="w")
        row += 1
        
        ttk.Label(stat_frame, text="Full Charges:").grid(row=row, column=0, sticky="w", padx=(0, 10), pady=5)
        ttk.Label(stat_frame, text=f"{stats['full_charges']}").grid(row=row, column=1, sticky="w")
        row += 1
        
        if stats['average_daily_usage'] is not None:
            ttk.Label(stat_frame, text="Average Daily Usage:").grid(row=row, column=0, sticky="w", padx=(0, 10), pady=5)
            ttk.Label(stat_frame, text=f"{stats['average_daily_usage']:.2f}%").grid(row=row, column=1, sticky="w")
            row += 1
        
        if stats['longest_session'] is not None:
            ttk.Label(stat_frame, text="Longest Battery Session:").grid(row=row, column=0, sticky="w", padx=(0, 10), pady=5)
            ttk.Label(stat_frame, text=f"{stats['longest_session']:.2f} hours").grid(row=row, column=1, sticky="w")
        
        # If no stats available
        if not any(value is not None and value != 0 for value in stats.values()):
            ttk.Label(stat_frame, text=f"No data available for the last {days} days", 
                    font=("Arial", 12)).grid(row=row, column=0, columnspan=2, pady=20)


def launch_gui():
    """Launch the PowerPulse GUI"""
    root = tk.Tk()
    app = PowerPulseGUI(root)
    root.mainloop()
