"""
CLI functionality for PowerPulse

This module implements the command-line interface for the application.
"""

import os
import sys
import time
import argparse
import threading

from powerpulse.battery import get_battery_info
from powerpulse.database import (
    setup_database, save_battery_info, get_notification_settings,
    update_notification_setting, clear_old_history
)
from powerpulse.stats import calculate_statistics, generate_history_plot
from powerpulse.notifications import check_notifications
from powerpulse.gui import launch_gui


def cli_monitor(args):
    """CLI monitoring mode"""
    setup_database()
    
    print(f"PowerPulse Battery Monitor")
    print(f"Monitoring every {args.interval} seconds. Press Ctrl+C to exit.")
    
    try:
        while True:
            info = get_battery_info()
            if info:
                save_battery_info(info)
                check_notifications(info)
                print(f"\rBattery: {info['percentage']}% - {'Charging' if info['is_charging'] else 'Discharging'}", end='')
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


def cli_stats(args):
    """Display battery statistics"""
    setup_database()
    
    days = args.days
    stats = calculate_statistics(days)
    
    print(f"\nBattery Statistics (Last {days} days)")
    print(f"----------------------------------------")
    
    if stats['average_discharge_rate'] is not None:
        print(f"Average Discharge Rate: {stats['average_discharge_rate']:.2f}% per hour")
    else:
        print(f"Average Discharge Rate: No data")
        
    if stats['average_charge_rate'] is not None:
        print(f"Average Charge Rate: {stats['average_charge_rate']:.2f}% per hour") 
    else:
        print(f"Average Charge Rate: No data")
        
    print(f"Discharge/Charge Cycles: {stats['discharge_cycles']}")
    print(f"Full Charges: {stats['full_charges']}")
    
    if stats['average_daily_usage'] is not None:
        print(f"Average Daily Usage: {stats['average_daily_usage']:.2f}%")
    else:
        print(f"Average Daily Usage: No data")
        
    if stats['longest_session'] is not None:
        print(f"Longest Battery Session: {stats['longest_session']:.2f} hours")
    else:
        print(f"Longest Battery Session: No data")


def cli_plot(args):
    """Generate and show a battery history plot"""
    setup_database()
    
    days = args.days
    fig = generate_history_plot(days)
    
    if fig:
        print(f"Generating battery history plot for the last {days} days...")
        import matplotlib.pyplot as plt
        plt.show()
    else:
        print(f"No data available for the specified period.")


def cli_info(args):
    """Display current battery information"""
    info = get_battery_info()
    
    if not info:
        print("Could not retrieve battery information.")
        return
    
    print("\nCurrent Battery Information")
    print(f"----------------------------------------")
    print(f"Battery Level: {info['percentage']}%")
    print(f"Status: {'Charging' if info['is_charging'] else 'Discharging'}")
    print(f"Power Connected: {'Yes' if info['power_plugged'] else 'No'}")
    
    if info['temperature']:
        print(f"Temperature: {info['temperature']}°C")
    
    if info['remaining_time'] and info['remaining_time'] > 0:
        hours = int(info['remaining_time'] / 3600)
        minutes = int((info['remaining_time'] % 3600) / 60)
        print(f"Estimated {'Time to Full' if info['is_charging'] else 'Time Remaining'}: {hours}h {minutes}m")


def cli_notification(args):
    """Configure notification settings"""
    setup_database()
    
    if args.list:
        settings = get_notification_settings()
        
        print("\nNotification Settings")
        print(f"----------------------------------------")
        for notification_type, level, enabled in settings:
            status = "Enabled" if enabled else "Disabled"
            print(f"{notification_type}: {level}% - {status}")
    
    elif args.type and args.level is not None:
        # Update notification level
        update_notification_setting(args.type, args.level)
        print(f"Updated {args.type} notification level to {args.level}%")
    
    elif args.type and args.enable is not None:
        # Enable/disable notification
        update_notification_setting(args.type, enabled=args.enable)
        print(f"{'Enabled' if args.enable else 'Disabled'} {args.type} notifications")
    
    else:
        print("Use --list to see current settings or provide --type and --level/--enable/--disable.")


def cli_cleanup(args):
    """Clean up old history data"""
    setup_database()
    days = args.days
    
    deleted = clear_old_history(days)
    print(f"Cleaned up {deleted} records older than {days} days.")


def cli_service(args):
    """Run PowerPulse as a background service"""
    # Ensure the database is set up
    setup_database()
    
    print(f"Starting PowerPulse service (interval: {args.interval} seconds)")
    
    # Create a daemon thread for monitoring
    def monitoring_service():
        while True:
            try:
                info = get_battery_info()
                if info:
                    save_battery_info(info)
                    check_notifications(info)
                time.sleep(args.interval)
            except Exception as e:
                print(f"Error in monitoring service: {e}")
                time.sleep(30)  # Shorter retry interval on error
    
    # Create and start the thread
    monitor_thread = threading.Thread(target=monitoring_service, daemon=True)
    monitor_thread.start()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("Service stopped.")


def main():
    """Main entry point for PowerPulse CLI"""
    parser = argparse.ArgumentParser(description="PowerPulse - A Battery Monitoring Tool")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor battery status")
    monitor_parser.add_argument("--interval", type=int, default=30, help="Monitoring interval in seconds")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Display current battery information")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Display battery statistics")
    stats_parser.add_argument("--days", type=int, default=7, help="Number of days to analyze")
    
    # Plot command
    plot_parser = subparsers.add_parser("plot", help="Show battery history plot")
    plot_parser.add_argument("--days", type=int, default=7, help="Number of days to plot")
    
    # Notification command
    notif_parser = subparsers.add_parser("notification", help="Configure notifications")
    notif_parser.add_argument("--list", action="store_true", help="List current notification settings")
    notif_parser.add_argument("--type", choices=["low_battery", "full_charge", "custom_level"], help="Notification type")
    notif_parser.add_argument("--level", type=int, help="Battery level for notification")
    notif_parser.add_argument("--enable", action="store_true", dest="enable", help="Enable notification")
    notif_parser.add_argument("--disable", action="store_false", dest="enable", help="Disable notification")
    notif_parser.set_defaults(enable=None)
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old history data")
    cleanup_parser.add_argument("--days", type=int, default=30, help="Keep data newer than this many days")
    
    # Service command
    service_parser = subparsers.add_parser("service", help="Run as a background service")
    service_parser.add_argument("--interval", type=int, default=60, help="Monitoring interval in seconds")
    
    # GUI command
    gui_parser = subparsers.add_parser("gui", help="Launch the GUI")
    
    # Parse arguments
    parser.add_argument("--gui", action="store_true", help="Launch the GUI (shortcut)")
    parser.add_argument("--version", action="store_true", help="Show version information")
    
    args = parser.parse_args()
    
    # Set up the database on first run
    setup_database()
    
    # Handle version request
    if args.version:
        from powerpulse import __version__
        print(f"PowerPulse v{__version__}")
        print("A lightweight, cross-platform battery monitoring tool")
        print("Copyright (c) 2025 Naveen Vasudevan")
        return
    
    # Execute the appropriate command
    if args.command == "monitor":
        cli_monitor(args)
    elif args.command == "info":
        cli_info(args)
    elif args.command == "stats":
        cli_stats(args)
    elif args.command == "plot":
        cli_plot(args)
    elif args.command == "notification":
        cli_notification(args)
    elif args.command == "cleanup":
        cli_cleanup(args)
    elif args.command == "service":
        cli_service(args)
    elif args.command == "gui" or args.gui:
        launch_gui()
    else:
        # Default: show info if no command specified
        if hasattr(args, 'interval'):
            cli_monitor(args)
        else:
            # Create a default args object with default interval
            class DefaultArgs:
                interval = 30
            cli_info(DefaultArgs())
            parser.print_help()


if __name__ == "__main__":
    main()
