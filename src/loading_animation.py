#!/usr/bin/env python3
import threading
import time
import sys
import itertools
import random


class LoadingAnimation:
    """ASCII loading animations for long-running operations"""
    
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = None
        self._last_line_length = 0
    
    def _clear_line(self):
        """Clear the current line"""
        sys.stdout.write('\r' + ' ' * self._last_line_length + '\r')
        sys.stdout.flush()
        self._last_line_length = 0
    
    def _man_running(self):
        """Man running animation"""
        frames = [
            "- - - - 🏃",
            "- - - 🏃 -", 
            "- - 🏃 - -",
            "- 🏃 - - -",
            "🏃 - - - -"
        ]
        message = "🤖 AI is thinking"
        
        while not self._stop_event.is_set():
            for frame in frames:
                if self._stop_event.is_set():
                    break
                self._clear_line()
                text = f"{message} {frame}"
                sys.stdout.write(text)
                sys.stdout.flush()
                self._last_line_length = len(text)
                time.sleep(0.3)
    
    def _loading_dots(self):
        """Simple loading dots animation"""
        dots = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        message = "🤖 AI is analyzing"
        
        while not self._stop_event.is_set():
            for dot in dots:
                if self._stop_event.is_set():
                    break
                self._clear_line()
                text = f"{message} {dot}"
                sys.stdout.write(text)
                sys.stdout.flush()
                self._last_line_length = len(text)
                time.sleep(0.1)
    
    def _progress_bar(self):
        """Progress bar animation"""
        bar_chars = "░▒▓█"
        message = "🤖 AI processing"
        
        while not self._stop_event.is_set():
            for i in range(21):  # 0 to 20
                if self._stop_event.is_set():
                    break
                filled = i // 5
                partial = i % 5
                bar = "█" * filled + (bar_chars[partial] if partial < 3 else "█")
                bar = bar.ljust(4, "░")
                self._clear_line()
                text = f"{message} [{bar}] {i*5}%"
                sys.stdout.write(text)
                sys.stdout.flush()
                self._last_line_length = len(text)
                time.sleep(0.15)
    
    def _matrix_rain(self):
        """Matrix-style falling characters"""
        chars = "01"
        message = "🤖 AI computing"
        
        while not self._stop_event.is_set():
            for _ in range(10):
                if self._stop_event.is_set():
                    break
                rain = ''.join(random.choice(chars) for _ in range(8))
                self._clear_line()
                text = f"{message} [{rain}]"
                sys.stdout.write(text)
                sys.stdout.flush()
                self._last_line_length = len(text)
                time.sleep(0.2)
    
    def _brain_activity(self):
        """Brain activity animation"""
        frames = [
            "🧠💭",
            "🧠✨", 
            "🧠⚡",
            "🧠💡",
            "🧠🔮"
        ]
        message = "🤖 AI thinking"
        
        while not self._stop_event.is_set():
            for frame in frames:
                if self._stop_event.is_set():
                    break
                self._clear_line()
                text = f"{message} {frame}"
                sys.stdout.write(text)
                sys.stdout.flush()
                self._last_line_length = len(text)
                time.sleep(0.4)
    
    def start(self, animation_type="run"):
        """Start the loading animation
        
        Args:
            animation_type: Type of animation ("run", "dots", "progress", "matrix", "brain")
        """
        if self._thread and self._thread.is_alive():
            return
        
        self._stop_event.clear()
        
        animation_map = {
            "run": self._man_running,
            "dots": self._loading_dots,
            "progress": self._progress_bar,
            "matrix": self._matrix_rain,
            "brain": self._brain_activity
        }
        
        animation_func = animation_map.get(animation_type, self._man_running)
        self._thread = threading.Thread(target=animation_func, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the loading animation and clear the line"""
        if self._thread and self._thread.is_alive():
            self._stop_event.set()
            self._thread.join(timeout=0.5)
        
        # Clear the entire line and move to beginning
        sys.stdout.write('\r' + ' ' * 100 + '\r')
        sys.stdout.flush()


# Context manager for easy usage
class LoadingContext:
    """Context manager for loading animations"""
    
    def __init__(self, animation_type="dots"):
        self.animation = LoadingAnimation()
        self.animation_type = animation_type
    
    def __enter__(self):
        self.animation.start(self.animation_type)
        return self.animation
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.animation.stop()
