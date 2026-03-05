#!/usr/bin/env python3
"""
Cross-platform FancyGit launcher script.
Detects the operating system and runs the appropriate startup script.
"""

import os
import platform
import subprocess
import sys


def detect_os():
    """Detect the current operating system."""
    system = platform.system().lower()
    
    if system == "linux":
        return "linux"
    elif system == "darwin":
        return "macos"
    elif system == "windows":
        return "windows"
    else:
        return "unknown"


def run_script(script_name):
    """Run the specified script."""
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    
    if not os.path.exists(script_path):
        print(f"❌ Error: {script_name} not found in the current directory")
        return False
    
    print(f"🚀 Running {script_name}...")
    
    try:
        if script_name.endswith('.sh'):
            # For Unix-like systems
            subprocess.run(['bash', script_path], check=True)
        elif script_name.endswith('.bat'):
            # For Windows
            subprocess.run([script_path], check=True, shell=True)
        
        print(f"✅ {script_name} completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running {script_name}: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Error: Could not find interpreter for {script_name}")
        return False


def main():
    """Main function to detect OS and run appropriate script."""
    print("🔍 Detecting operating system...")
    
    os_type = detect_os()
    
    if os_type == "linux":
        print("✅ Linux detected")
        run_script("start.sh")
    elif os_type == "macos":
        print("✅ macOS detected")
        run_script("start.sh")
    elif os_type == "windows":
        print("✅ Windows detected")
        run_script("start.bat")
    else:
        print(f"❌ Unsupported operating system: {platform.system()}")
        print("Supported systems: Linux, macOS, Windows")
        sys.exit(1)


if __name__ == "__main__":
    main()
