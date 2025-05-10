use eframe::{egui, epi};
use crate::{battery_monitor::BatteryMonitor, database::Database};

pub struct PowerPulseApp {
    monitor: BatteryMonitor,
    db: Database,
    current_tab: Tab,
}

enum Tab {
    Status,
    History,
    Settings,
}

impl epi::App for PowerPulseApp {
    fn name(&self) -> &str {
        "PowerPulse"
    }
    
    fn update(&mut self, ctx: &egui::Context, _frame: &epi::Frame) {
        // GUI code will go here
    }
}