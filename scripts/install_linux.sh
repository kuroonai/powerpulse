#!/bin/bash

# PowerPulse Installer for Linux
echo "PowerPulse Installer for Linux"
echo "=============================="
echo ""

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This installer requires root privileges."
    echo "Please run with sudo: sudo ./install_linux.sh"
    echo ""
    exit 1
fi

# Determine Python path
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    PYTHON_CMD=python
else
    echo "ERROR: Python not found. Please install Python 3.8 or newer."
    echo "Run: sudo apt-get install python3 python3-pip python3-venv  # For Debian/Ubuntu"
    echo "  or: sudo dnf install python3 python3-pip  # For Fedora"
    echo ""
    exit 1
fi

# Get Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
echo "Found Python $PYTHON_VERSION"
echo ""

# Create installation directory
INSTALL_DIR=/opt/powerpulse
mkdir -p "$INSTALL_DIR"
echo "Installing to $INSTALL_DIR..."
echo ""

# Copy AppImage or install from source
if [ -f "PowerPulse-Linux.AppImage" ]; then
    echo "Installing AppImage..."
    cp "PowerPulse-Linux.AppImage" "$INSTALL_DIR/PowerPulse"
    chmod +x "$INSTALL_DIR/PowerPulse"
else
    echo "Installing from source..."
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv "$INSTALL_DIR/venv"
    
    echo "Installing PowerPulse..."
    "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
    "$INSTALL_DIR/venv/bin/pip" install .
    
    # Create launcher script
    cat > "$INSTALL_DIR/PowerPulse" << EOF
#!/bin/bash
$INSTALL_DIR/venv/bin/python -m powerpulse "\$@"
EOF
    chmod +x "$INSTALL_DIR/PowerPulse"
fi

# Create symlink in /usr/local/bin
echo "Creating symlink in /usr/local/bin..."
ln -sf "$INSTALL_DIR/PowerPulse" /usr/local/bin/powerpulse

# Create desktop entry
echo "Creating desktop entry..."
mkdir -p /usr/share/applications
cat > /usr/share/applications/powerpulse.desktop << EOF
[Desktop Entry]
Name=PowerPulse
Comment=Battery Monitoring Tool
Exec=$INSTALL_DIR/PowerPulse --gui
Icon=$INSTALL_DIR/icon.png
Terminal=false
Type=Application
Categories=Utility;System;
Keywords=battery;monitor;power;
EOF

# Create icon
if [ -f "resources/powerpulse.png" ]; then
    cp "resources/powerpulse.png" "$INSTALL_DIR/icon.png"
else
    # Create a simple placeholder icon if none exists
    echo "Creating placeholder icon..."
    cat > "$INSTALL_DIR/icon.png" << EOF
