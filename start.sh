#!/bin/bash

# FancyGit Installation Script
# This script sets up FancyGit for system-wide use

echo "🚀 Setting up FancyGit..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.6+ first."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.6"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python $python_version is too old. Please install Python 3.6 or higher."
    exit 1
fi

echo "✅ Python $python_version detected"

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install Git first."
    exit 1
fi

echo "✅ Git detected"

# Make fancygit.py executable
echo "🔧 Making fancygit.py executable..."
chmod +x fancygit.py

if [ $? -eq 0 ]; then
    echo "✅ fancygit.py is now executable"
else
    echo "❌ Failed to make fancygit.py executable"
    exit 1
fi

# Create system-wide symlink
echo "🔗 Creating system-wide symlink..."
sudo ln -sf "$(pwd)/fancygit.py" /usr/local/bin/fancygit

if [ $? -eq 0 ]; then
    echo "✅ Symlink created successfully"
else
    echo "❌ Failed to create symlink. Please run with sudo privileges."
    exit 1
fi

# Test the installation
echo "🧪 Testing installation..."
if command -v fancygit &> /dev/null; then
    echo "✅ FancyGit is now available system-wide!"
    echo ""
    echo "📖 Usage examples:"
    echo "  fancygit add ."
    echo "  fancygit commit -m 'Your message'"
    echo "  fancygit push origin main"
    echo "  fancygit pull origin main"
    echo ""
    echo "🎉 Installation complete! You can now use FancyGit from anywhere."
else
    echo "❌ Installation verification failed"
    exit 1
fi
