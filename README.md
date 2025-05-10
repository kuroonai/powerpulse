# PowerPulse

<div align="center">
  <img src="https://via.placeholder.com/150/0000FF/FFFFFF?text=PowerPulse" alt="PowerPulse Logo" width="150" height="150">
  
  ![GitHub license](https://img.shields.io/github/license/kuroonai/powerpulse)
  ![GitHub stars](https://img.shields.io/github/stars/kuroonai/powerpulse)
  ![GitHub forks](https://img.shields.io/github/forks/kuroonai/powerpulse)
  ![GitHub issues](https://img.shields.io/github/issues/kuroonai/powerpulse)
</div>

## About

PowerPulse is a lightweight, cross-platform battery monitoring tool designed to track, store, and visualize your device's battery information. Keep tabs on your battery's charge cycles, analyze usage patterns, and receive timely notifications to optimize battery life.

## Features

- **Real-time Battery Monitoring**: Track charge level, charging status, and estimated time remaining
- **Historical Data**: Store and visualize your battery's history over time
- **Statistical Analysis**: Gain insights from discharge rates, cycle counts, and usage patterns
- **Customizable Notifications**: Get alerts for low battery, full charge, or custom thresholds
- **Dual Interface**: Use either the intuitive GUI or efficient CLI
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Lightweight**: Minimal resource usage while running in the background

## Installation

### Binary Releases

Download the latest executable for your platform from the [releases page](https://github.com/kuroonai/powerpulse/releases).

### From Source

```bash
# Clone the repository
git clone https://github.com/kuroonai/powerpulse.git
cd powerpulse

# Install with pip
pip install .

# Or for development
pip install -e ".[dev]"
```

## Quick Start

### GUI Mode

```bash
# Launch the graphical interface
powerpulse --gui
```

### CLI Mode

```bash
# Show current battery information
powerpulse info

# Start monitoring with 30-second intervals
powerpulse monitor --interval 30

# Display statistics for the last 7 days
powerpulse stats --days 7

# Show battery history graph
powerpulse plot --days 14

# Configure notifications
powerpulse notification --list
powerpulse notification --type low_battery --level 15 --enable
```

## Screenshots

![PowerPulse GUI](https://via.placeholder.com/800x450/0000FF/FFFFFF?text=PowerPulse+GUI)

## Development

### Requirements

- Python 3.8+
- Dependencies listed in `requirements.txt`

### Setting Up Development Environment

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt
```

### Running Tests

```bash
pytest
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

- **Naveen Vasudevan** - [kuroonai](https://github.com/kuroonai)

## Acknowledgments

- Thanks to all contributors who have helped shape PowerPulse
- Inspired by the need for better battery management across platforms
