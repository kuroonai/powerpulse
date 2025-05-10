"""
Statistics and analysis functions for PowerPulse

This module provides functions for calculating battery usage statistics
and generating plots based on historical data.
"""

import datetime
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter

from powerpulse.database import get_battery_history


def calculate_statistics(days=7):
    """Calculate battery usage statistics"""
    history = get_battery_history(days)
    
    if not history:
        return {
            'average_discharge_rate': None,
            'average_charge_rate': None,
            'discharge_cycles': 0,
            'full_charges': 0,
            'average_daily_usage': None,
            'longest_session': None
        }
    
    # Convert history to structured data
    timestamps = []
    percentages = []
    is_charging = []
    
    for entry in history:
        timestamps.append(datetime.datetime.fromisoformat(entry[0]))
        percentages.append(entry[1])
        is_charging.append(bool(entry[2]))
    
    # Initialize statistics
    stats = {
        'average_discharge_rate': None,
        'average_charge_rate': None,
        'discharge_cycles': 0,
        'full_charges': 0,
        'average_daily_usage': None,
        'longest_session': None
    }
    
    # Calculate discharge and charge rates
    discharge_rates = []
    charge_rates = []
    
    for i in range(1, len(timestamps)):
        time_diff = (timestamps[i] - timestamps[i-1]).total_seconds() / 3600  # in hours
        if time_diff <= 0:
            continue
            
        percentage_diff = percentages[i] - percentages[i-1]
        rate = percentage_diff / time_diff  # % per hour
        
        if is_charging[i] and percentage_diff > 0:
            charge_rates.append(rate)
        elif not is_charging[i] and percentage_diff < 0:
            discharge_rates.append(-rate)  # Make positive for easier interpretation
    
    stats['average_discharge_rate'] = np.mean(discharge_rates) if discharge_rates else None
    stats['average_charge_rate'] = np.mean(charge_rates) if charge_rates else None
    
    # Count charging cycles (a cycle is when charging starts after discharging)
    cycle_count = 0
    last_was_charging = None
    
    for i in range(len(is_charging)):
        if last_was_charging is not None and not last_was_charging and is_charging[i]:
            cycle_count += 1
        last_was_charging = is_charging[i]
    
    stats['discharge_cycles'] = cycle_count
    
    # Count full charges (when battery reaches 100% while charging)
    full_charges = 0
    for i in range(1, len(percentages)):
        if is_charging[i] and percentages[i] >= 99.5 and percentages[i-1] < 99.5:
            full_charges += 1
    
    stats['full_charges'] = full_charges
    
    # Calculate average daily usage (how much battery % is used per day)
    if len(timestamps) >= 2:
        total_days = (timestamps[-1] - timestamps[0]).total_seconds() / (24 * 3600)
        if total_days > 0:
            # Sum of all discharge percentages
            total_discharge = 0
            for i in range(1, len(percentages)):
                diff = percentages[i] - percentages[i-1]
                if diff < 0:
                    total_discharge -= diff
            
            stats['average_daily_usage'] = total_discharge / total_days
    
    # Find longest session on battery
    if len(timestamps) >= 2:
        longest_session = 0
        current_session = 0
        session_start = None
        
        for i in range(len(is_charging)):
            if not is_charging[i]:
                if session_start is None:
                    session_start = timestamps[i]
            else:
                if session_start is not None:
                    session_duration = (timestamps[i] - session_start).total_seconds() / 3600
                    longest_session = max(longest_session, session_duration)
                    session_start = None
        
        # Check if we're still in a session at the end
        if session_start is not None:
            session_duration = (timestamps[-1] - session_start).total_seconds() / 3600
            longest_session = max(longest_session, session_duration)
        
        stats['longest_session'] = longest_session
    
    return stats


def generate_history_plot(days=7):
    """Generate a plot of battery history"""
    history = get_battery_history(days)
    
    if not history:
        return None
    
    timestamps = []
    percentages = []
    charging_status = []
    
    for entry in history:
        timestamps.append(datetime.datetime.fromisoformat(entry[0]))
        percentages.append(entry[1])
        charging_status.append(bool(entry[2]))
    
    fig, ax = plt.figure(figsize=(10, 5)), plt.gca()
    
    # Plot battery percentage
    ax.plot(timestamps, percentages, 'b-', label='Battery %')
    
    # Highlight charging periods
    charge_starts = []
    charge_ends = []
    in_charge = False
    
    for i, charging in enumerate(charging_status):
        if charging and not in_charge:
            charge_starts.append(i)
            in_charge = True
        elif not charging and in_charge:
            charge_ends.append(i)
            in_charge = False
    
    # If still charging at the end
    if in_charge:
        charge_ends.append(len(timestamps) - 1)
    
    # Create patches for charging periods
    for start, end in zip(charge_starts, charge_ends):
        if start < len(timestamps) and end < len(timestamps):
            ax.axvspan(timestamps[start], timestamps[end], alpha=0.2, color='green', 
                      label='_' if start > 0 else 'Charging')
    
    ax.set_ylim(0, 100)
    ax.set_xlabel('Time')
    ax.set_ylabel('Battery Percentage')
    ax.set_title(f'Battery History (Last {days} Days)')
    ax.xaxis.set_major_formatter(DateFormatter('%m-%d %H:%M'))
    ax.grid(True, alpha=0.3)
    
    # Add legend only if there are charging periods
    if charge_starts:
        ax.legend()
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig


def generate_daily_usage_plot(days=7):
    """Generate a plot of daily battery usage"""
    history = get_battery_history(days)
    
    if not history:
        return None
    
    # Group data by day
    daily_data = {}
    
    for entry in history:
        timestamp = datetime.datetime.fromisoformat(entry[0])
        date = timestamp.date()
        
        if date not in daily_data:
            daily_data[date] = {
                'min': 100,
                'max': 0,
                'charging_time': 0,
                'samples': 0
            }
        
        # Update min/max percentage
        percentage = entry[1]
        daily_data[date]['min'] = min(daily_data[date]['min'], percentage)
        daily_data[date]['max'] = max(daily_data[date]['max'], percentage)
        
        # Count charging time
        if bool(entry[2]):  # is_charging
            daily_data[date]['charging_time'] += 1
        
        daily_data[date]['samples'] += 1
    
    # Calculate daily usage and charging percentage
    dates = sorted(daily_data.keys())
    daily_usage = []
    charging_percentage = []
    
    for date in dates:
        data = daily_data[date]
        # Daily usage is the difference between max and min
        usage = data['max'] - data['min']
        daily_usage.append(usage)
        
        # Charging percentage is the percentage of time spent charging
        if data['samples'] > 0:
            charging_percentage.append((data['charging_time'] / data['samples']) * 100)
        else:
            charging_percentage.append(0)
    
    # Create the plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    
    # Daily usage plot
    ax1.bar(dates, daily_usage, color='blue', alpha=0.7)
    ax1.set_ylabel('Battery Usage (%)')
    ax1.set_title(f'Daily Battery Usage (Last {days} Days)')
    ax1.grid(True, alpha=0.3)
    
    # Charging time plot
    ax2.bar(dates, charging_percentage, color='green', alpha=0.7)
    ax2.set_xlabel('Date')
    ax2.set_ylabel('Time Spent Charging (%)')
    ax2.set_title('Daily Charging Time')
    ax2.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return fig
