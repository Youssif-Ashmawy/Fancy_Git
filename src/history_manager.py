'''History Manager for tracking user interactions with git commands'''
import json
from pathlib import Path
import os

class HistoryManager:
    def __init__(self) -> None:
        # Define a path for the history file in the current working directory under a .fancygit folder
        self.history_file = Path.cwd() / '.fancygit' / 'history.json'
        # Ensure the directory exists
        self.history_file.parent.mkdir(parents=True, exist_ok=True)


    def _load_history(self):
        '''Load history from the JSON file'''
        if self.history_file.exists():
            with open(self.history_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_history(self, history):
        '''Write whatever is in the history list to the JSON file'''
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)

    def add_entry(self, command):
        '''Loads the history, appends a new entry, and saves it back to the file'''
        history = self._load_history()
        history.append({
            'command': command,
            'timestamp': os.path.getmtime(self.history_file) if self.history_file.exists() else None
        })
        self._save_history(history)

    def get_history(self):
        '''Return the entire history'''
        return self._load_history()
    
    def clear_history(self):
        '''Clear the history by saving an empty list to the file'''
        self._save_history([])