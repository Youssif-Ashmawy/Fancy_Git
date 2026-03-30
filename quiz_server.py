#!/usr/bin/env python3
import sys
import os
import time
import signal

# Add current directory to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from fancygit import FancyGit

def signal_handler(sig, frame):
    print('\n🛑 Shutting down quiz server...')
    sys.exit(0)

def main():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🚀 Starting FancyGit Quiz Server...")
    
    fg = FancyGit()
    
    # Launch the quiz
    if fg.quiz_manager.launch_quiz():
        print(f"🌐 Quiz server running on: http://127.0.0.1:{fg.quiz_manager._quiz_server_port}/quiz")
        print("📝 Press Ctrl+C to stop the server")
        
        # Keep the server running
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print('\n🛑 Shutting down quiz server...')
    else:
        print("❌ Failed to start quiz server")
        sys.exit(1)

if __name__ == "__main__":
    main()
