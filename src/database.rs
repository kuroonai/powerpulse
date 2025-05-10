use rusqlite::{params, Connection, Result};
use crate::battery_monitor::BatteryStatus;
use std::path::Path;

pub struct Database {
    conn: Connection,
}

impl Database {
    pub fn new(db_path: &str) -> Result<Self> {
        let path = Path::new(db_path);
        // Create parent directories if they don't exist
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }

        let conn = Connection::open(db_path)?;
        
        // Create tables if they don't exist
        conn.execute(
            "CREATE TABLE IF NOT EXISTS battery_history (
                id INTEGER PRIMARY KEY,
                timestamp TEXT NOT NULL,
                percentage REAL NOT NULL,
                state TEXT NOT NULL,
                time_to_empty INTEGER,
                time_to_full INTEGER
            )",
            [],
        )?;

        Ok(Self { conn })
    }

    pub fn save_status(&self, status: &BatteryStatus) -> Result<()> {
        self.conn.execute(
            "INSERT INTO battery_history (timestamp, percentage, state, time_to_empty, time_to_full)
             VALUES (?1, ?2, ?3, ?4, ?5)",
            params![
                status.timestamp.to_rfc3339(),
                status.percentage,
                status.state,
                status.time_to_empty,
                status.time_to_full
            ],
        )?;
        Ok(())
    }

    pub fn get_recent_history(&self, limit: usize) -> Result<Vec<BatteryStatus>> {
        let mut stmt = self.conn.prepare(
            "SELECT timestamp, percentage, state, time_to_empty, time_to_full 
             FROM battery_history 
             ORDER BY timestamp DESC 
             LIMIT ?1"
        )?;

        let history_iter = stmt.query_map([limit as i64], |row| {
            Ok(BatteryStatus {
                timestamp: chrono::DateTime::parse_from_rfc3339(&row.get::<_, String>(0)?)
                    .unwrap()
                    .with_timezone(&chrono::Local),
                percentage: row.get(1)?,
                state: row.get(2)?,
                time_to_empty: row.get(3)?,
                time_to_full: row.get(4)?,
            })
        })?;

        let mut history = Vec::new();
        for status in history_iter {
            history.push(status?);
        }
        Ok(history)
    }
}