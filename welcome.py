#!/usr/bin/env python3
"""
FancyGit Welcome Message Script
Displays the cool ASCII art welcome message
"""
from src.colors import Colors, color_header, color_info

def show_welcome():
    """Display the FancyGit welcome message with colors"""
    print(Colors.colorize(r"""
     /$$$$$$$$ /$$$$$$  /$$   /$$  /$$$$$$  /$$     /$$ /$$$$$$  /$$$$$$ /$$$$$$$$
    | $$_____//$$__  $$| $$$ | $$ /$$__  $$|  $$   /$$//$$__  $$|_  $$_/|__  $$__/
    | $$     | $$  \ $$| $$$$| $$| $$  \__/ \  $$ /$$/| $$  \__/  | $$     | $$   
    | $$$$$  | $$$$$$$$| $$ $$ $$| $$        \  $$$$/ | $$ /$$$$  | $$     | $$   
    | $$__/  | $$__  $$| $$  $$$$| $$         \  $$/  | $$|_  $$  | $$     | $$   
    | $$     | $$  | $$| $$\  $$$| $$    $$    | $$   | $$  \ $$  | $$     | $$   
    | $$     | $$  | $$| $$ \  $$|  $$$$$$/    | $$   |  $$$$$$/ /$$$$$$   | $$   
    |__/     |__/  |__/|__/  \__/ \______/     |__/    \______/ |______/   |__/
    """, Colors.BRIGHT_YELLOW))
    
    print(color_info(f"{'*'*22} ") + color_header("🚀 FancyGit - Enhanced Git Experience") + color_info(f" {'*'*22}"))
    print()

if __name__ == "__main__":
    show_welcome()
