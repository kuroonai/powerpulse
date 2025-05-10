#!/usr/bin/env python
"""
PowerPulse Executable Builder Script
-----------------------------------
This script builds standalone executables for PowerPulse using PyInstaller.
Supported platforms:
- Windows (.exe)
- Linux (.AppImage)
"""

import os
import sys
import platform
import argparse
import subprocess
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.absolute()


def ensure_resources():
    """Ensure that resource files exist or create placeholders."""
    resources_dir = REPO_ROOT / "resources"
    resources_dir.mkdir(exist_ok=True)
    
    # Create icon placeholder if it doesn't exist
    icon_file = resources_dir / "powerpulse.ico"
    if not icon_file.exists():
        try:
            # Try to create a simple icon
            from PIL import Image, ImageDraw
            
            img = Image.new('RGBA', (256, 256), color=(0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.ellipse((20, 20, 236, 236), fill=(0, 120, 212))
            draw.rectangle((108, 60, 148, 196), fill=(255, 255, 255))
            img.save(icon_file, format='ICO')
            
            # Also create PNG version for Linux
            img.save(resources_dir / "powerpulse.png", format='PNG')
            
            print(f"Created placeholder icon at {icon_file}")
        except ImportError:
            print("Pillow not installed. Creating empty icon files.")
            # Create empty files
            icon_file.touch()
            (resources_dir / "powerpulse.png").touch()


def build_windows_executable(args):
    """Build executable for Windows."""
    print("Building Windows executable...")
    
    cmd = [
        "pyinstaller",
        "--name=PowerPulse",
        "--onefile" if args.onefile else "--onedir",
        "--windowed" if not args.console else "",
        f"--icon={REPO_ROOT}/resources/powerpulse.ico",
        f"--add-data={REPO_ROOT}/powerpulse/resources;resources",
        f"{REPO_ROOT}/powerpulse/cli.py"
    ]
    
    # Remove empty strings
    cmd = [item for item in cmd if item]
    
    print(f"Running command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    
    output_file = "dist/PowerPulse.exe"
    if os.path.exists(output_file):
        print(f"Successfully created Windows executable: {output_file}")
    else:
        print("Failed to create Windows executable.")
        return False
    
    if args.zip:
        import zipfile
        zip_path = f"{REPO_ROOT}/PowerPulse-Windows.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            zipf.write(output_file, arcname="PowerPulse.exe")
        print(f"Created ZIP archive: {zip_path}")
    
    return True


def build_linux_executable(args):
    """Build executable for Linux."""
    print("Building Linux executable...")
    
    cmd = [
        "pyinstaller",
        "--name=PowerPulse",
        "--onefile" if args.onefile else "--onedir",
        "--windowed" if not args.console else "",
        f"--icon={REPO_ROOT}/resources/powerpulse.ico",
        f"--add-data={REPO_ROOT}/powerpulse/resources:resources",
        f"{REPO_ROOT}/powerpulse/cli.py"
    ]
    
    # Remove empty strings
    cmd = [item for item in cmd if item]
    
    print(f"Running command: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)
    
    output_file = "dist/PowerPulse"
    if os.path.exists(output_file):
        print(f"Successfully created Linux executable: {output_file}")
    else:
        print("Failed to create Linux executable.")
        return False
    
    if args.appimage:
        try:
            build_linux_appimage()
        except Exception as e:
            print(f"Failed to create AppImage: {e}")
            return False
    
    return True


def build_linux_appimage():
    """Build AppImage for Linux."""
    print("Building Linux AppImage...")
    
    # Create AppDir structure
    app_dir = Path(f"{REPO_ROOT}/AppDir")
    bin_dir = app_dir / "usr/bin"
    desktop_dir = app_dir / "usr/share/applications"
    icon_dir = app_dir / "usr/share/icons/hicolor/256x256/apps"
    
    bin_dir.mkdir(parents=True, exist_ok=True)
    desktop_dir.mkdir(parents=True, exist_ok=True)
    icon_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy executable
    shutil.copy(f"{REPO_ROOT}/dist/PowerPulse", bin_dir / "PowerPulse")
    
    # Create desktop entry
    with open(desktop_dir / "powerpulse.desktop", "w") as f:
        f.write("""[Desktop Entry]
Name=PowerPulse
Exec=PowerPulse
Icon=powerpulse
Type=Application
Categories=Utility;System;
""")
    
    # Copy icon
    shutil.copy(f"{REPO_ROOT}/resources/powerpulse.png", icon_dir / "powerpulse.png")
    shutil.copy(f"{REPO_ROOT}/resources/powerpulse.png", app_dir / "powerpulse.png")
    
    # Check if appimagetool is installed
    try:
        subprocess.run(["appimagetool", "--version"], check=True, capture_output=True)
        has_appimagetool = True
    except (subprocess.SubprocessError, FileNotFoundError):
        has_appimagetool = False
    
    if not has_appimagetool:
        print("Downloading appimagetool...")
        appimagetool_url = "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
        subprocess.run(["wget", "-O", "appimagetool", appimagetool_url], check=True)
        subprocess.run(["chmod", "+x", "appimagetool"], check=True)
        appimagetool_cmd = "./appimagetool"
    else:
        appimagetool_cmd = "appimagetool"
    
    # Build AppImage
    subprocess.run([appimagetool_cmd, "AppDir", "PowerPulse-Linux.AppImage"], check=True)
    
    if os.path.exists(f"{REPO_ROOT}/PowerPulse-Linux.AppImage"):
        print(f"Successfully created AppImage: {REPO_ROOT}/PowerPulse-Linux.AppImage")
    else:
        raise RuntimeError("Failed to create AppImage")


def main():
    """Main function to parse arguments and build executables."""
    parser = argparse.ArgumentParser(description="Build PowerPulse executables")
    parser.add_argument("--platform", choices=["auto", "windows", "linux"], default="auto",
                      help="Target platform (default: auto-detect)")
    parser.add_argument("--onefile", action="store_true", help="Create a single file executable")
    parser.add_argument("--console", action="store_true", help="Show console window (for debugging)")
    parser.add_argument("--appimage", action="store_true", help="Create AppImage for Linux")
    parser.add_argument("--zip", action="store_true", help="Create ZIP archive for Windows")
    
    args = parser.parse_args()
    
    # Auto-detect platform if not specified
    if args.platform == "auto":
        system = platform.system().lower()
        if system == "windows":
            args.platform = "windows"
        elif system == "linux":
            args.platform = "linux"
        else:
            print(f"Unsupported platform: {system}")
            sys.exit(1)
    
    # Ensure resource files exist
    ensure_resources()
    
    # Change to repository root
    os.chdir(REPO_ROOT)
    
    # Check for PyInstaller
    try:
        subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("PyInstaller not found. Please install it with: pip install pyinstaller")
        sys.exit(1)
    
    # Build for the selected platform
    if args.platform == "windows":
        success = build_windows_executable(args)
    elif args.platform == "linux":
        success = build_linux_executable(args)
    else:
        print(f"Unsupported platform: {args.platform}")
        sys.exit(1)
    
    if success:
        print("Build completed successfully!")
    else:
        print("Build failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
