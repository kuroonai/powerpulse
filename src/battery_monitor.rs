use battery::{Battery, Manager, State};
use chrono::{DateTime, Local};
use std::error::Error;

#[derive(Debug, Clone)]
pub struct BatteryStatus {
    pub timestamp: DateTime<Local>,
    pub percentage: f32,
    pub state: String,
    pub time_to_empty: Option<u32>,  // minutes
    pub time_to_full: Option<u32>,   // minutes
}

pub struct BatteryMonitor {
    manager: Manager,
}

impl BatteryMonitor {
    pub fn new() -> Result<Self, Box<dyn Error>> {
        let manager = Manager::new()?;
        Ok(Self { manager })
    }

    pub fn get_status(&self) -> Result<BatteryStatus, Box<dyn Error>> {
        let battery = self.manager.batteries()?.next()
            .ok_or("No battery found")??;
        
        Ok(BatteryStatus {
            timestamp: Local::now(),
            percentage: battery.state_of_charge().value * 100.0,
            state: match battery.state() {
                State::Charging => "Charging".to_string(),
                State::Discharging => "Discharging".to_string(),
                State::Empty => "Empty".to_string(),
                State::Full => "Full".to_string(),
                State::Unknown => "Unknown".to_string(),
                _ => "Other".to_string(),
            },
            time_to_empty: if battery.state() == State::Discharging {
                battery.time_to_empty().map(|t| t.value as u32 / 60)
            } else {
                None
            },
            time_to_full: if battery.state() == State::Charging {
                battery.time_to_full().map(|t| t.value as u32 / 60)
            } else {
                None
            },
        })
    }
}