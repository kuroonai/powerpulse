mod battery_monitor;
mod database;
mod notifications;

use crate::battery_monitor::BatteryMonitor;
use crate::database::Database;
use crate::notifications::BatteryNotifier;
use clap::Parser;
use std::{thread, time::Duration, path::PathBuf};

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Run as a background service
    #[arg(short, long)]
    daemon: bool,

    /// Show current battery status and exit
    #[arg(short, long)]
    status: bool,

    /// Custom notification thresholds (percent)
    #[arg(short, long, value_delimiter = ',', default_values_t = vec![20, 15, 10, 5])]
    thresholds: Vec<u8>,
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();
    
    // Determine data directory
    let data_dir = dirs::data_local_dir()
        .unwrap_or_else(|| PathBuf::from("."))
        .join("powerpulse");
    
    let db_path = data_dir.join("battery_history.db").to_str().unwrap().to_string();
    
    let monitor = BatteryMonitor::new()?;
    let db = Database::new(&db_path)?;
    let mut notifier = BatteryNotifier::new(args.thresholds);
    
    // Just show status and exit if requested
    if args.status {
        let status = monitor.get_status()?;
        println!("Battery status: {}%, {}", status.percentage, status.state);
        if let Some(time) = status.time_to_empty {
            println!("Time to empty: {} minutes", time);
        }
        if let Some(time) = status.time_to_full {
            println!("Time to full: {} minutes", time);
        }
        return Ok(());
    }
    
    // Run in the background if daemon mode is enabled
    if args.daemon {
        println!("PowerPulse is running in the background. Press Ctrl+C to exit.");
        
        // Main monitoring loop
        loop {
            match monitor.get_status() {
                Ok(status) => {
                    // Save status to database
                    if let Err(e) = db.save_status(&status) {
                        eprintln!("Error saving to database: {}", e);
                    }
                    
                    // Check notifications
                    let is_charging = status.state == "Charging";
                    if let Err(e) = notifier.check_and_notify(status.percentage, is_charging) {
                        eprintln!("Error sending notification: {}", e);
                    }
                },
                Err(e) => eprintln!("Error getting battery status: {}", e),
            }
            
            // Wait before next check
            thread::sleep(Duration::from_secs(60)); // Check every minute
        }
    } else {
        println!("Run with --daemon to start background monitoring");
        println!("Run with --status to check current battery status");
    }
    
    Ok(())
}