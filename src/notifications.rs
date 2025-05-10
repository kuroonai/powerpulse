use notify_rust::Notification;
use std::error::Error;

pub struct BatteryNotifier {
    last_notification_level: Option<u8>,
    notification_thresholds: Vec<u8>,
}

impl BatteryNotifier {
    pub fn new(thresholds: Vec<u8>) -> Self {
        Self {
            last_notification_level: None,
            notification_thresholds: thresholds,
        }
    }

    pub fn check_and_notify(&mut self, percentage: f32, charging: bool) -> Result<(), Box<dyn Error>> {
        let current_percentage = percentage as u8;
        
        // Check if we need to notify
        let should_notify = self.notification_thresholds.iter().any(|&threshold| {
            match self.last_notification_level {
                // First run or threshold crossed
                None => current_percentage <= threshold,
                // We've crossed below a threshold since last check
                Some(last) => last > threshold && current_percentage <= threshold,
            }
        });

        if should_notify && !charging {
            Notification::new()
                .summary("PowerPulse Battery Alert")
                .body(&format!("Battery level is at {}%", current_percentage))
                .icon("battery-low")
                .timeout(5000) // milliseconds
                .show()?;
        }

        self.last_notification_level = Some(current_percentage);
        Ok(())
    }
}