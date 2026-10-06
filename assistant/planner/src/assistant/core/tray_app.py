"""Aether System Tray Application

Provides a system tray icon for easy access to Aether's controls.
Features:
- Start/stop planner and wake listener
- Auto-start on boot option
- Quick access to dashboard
- Status indication
"""

import os
import sys
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional

try:
    import pystray
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False
    print("pystray not available. Install with: pip install pystray pillow")

from assistant.core.crash_handler import setup_global_crash_handler

# Set up crash handler
crash_handler = setup_global_crash_handler("Aether System Tray")


class AetherTrayApp:
    """System tray application for Aether."""
    
    def __init__(self):
        self.planner_process: Optional[subprocess.Popen] = None
        self.wake_process: Optional[subprocess.Popen] = None
        self.ollama_process: Optional[subprocess.Popen] = None
        self.dashboard_process: Optional[subprocess.Popen] = None
        # Use current working directory as base
        self.planner_dir = Path.cwd()
        self.base_dir = self.planner_dir.parent.parent
        self.venv_python = self.planner_dir / ".venv" / "Scripts" / "python.exe"
        self.running = True
        
        # Verify paths
        print(f"Current directory: {Path.cwd()}")
        print(f"Base directory: {self.base_dir}")
        print(f"Planner directory: {self.planner_dir}")
        print(f"Python path: {self.venv_python}")
        print(f"Python exists: {self.venv_python.exists()}")
        
        if not self.venv_python.exists():
            print(f"Warning: Virtual environment not found at {self.venv_python}")
            print("Please ensure the virtual environment is created.")
        
    def create_icon(self, size: int = 64) -> Image.Image:
        """Create a simple icon for the system tray."""
        # Create a blue circle with 'A' for Aether
        image = Image.new('RGB', (size, size), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw blue circle
        padding = 4
        draw.ellipse(
            [padding, padding, size - padding, size - padding],
            fill=(25, 118, 210, 255)
        )
        
        # Draw 'A'
        text_color = (255, 255, 255)
        # Simple 'A' shape
        margin = size // 4
        # Left line
        draw.line([margin, size - margin, size // 2, margin], fill=text_color, width=3)
        # Right line
        draw.line([size // 2, margin, size - margin, size - margin], fill=text_color, width=3)
        # Crossbar
        crossbar_y = size - size // 3
        draw.line([margin + 5, crossbar_y, size - margin - 5, crossbar_y], fill=text_color, width=3)
        
        return image
    
    def start_ollama(self):
        """Start Ollama service."""
        if self.ollama_process and self.ollama_process.poll() is None:
            print("Ollama is already running")
            return
        
        try:
            # Check if Ollama is already running
            import urllib.request
            req = urllib.request.Request("http://127.0.0.1:11434/api/tags", timeout=2)
            with urllib.request.urlopen(req):
                print("Ollama is already running")
                return
        except:
            pass
        
        print("Starting Ollama...")
        try:
            self.ollama_process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            print("Ollama started")
        except FileNotFoundError:
            print("Ollama not found. Please install Ollama from https://ollama.com/download")
    
    def stop_ollama(self):
        """Stop Ollama service."""
        if self.ollama_process:
            self.ollama_process.terminate()
            self.ollama_process = None
            print("Ollama stopped")
    
    def start_planner(self):
        """Start the planner listener."""
        if self.planner_process and self.planner_process.poll() is None:
            print("Planner is already running")
            return
        
        print(f"Starting planner from {self.planner_dir}...")
        print(f"Python path: {self.venv_python}")
        print(f"Python exists: {self.venv_python.exists()}")
        
        try:
            self.planner_process = subprocess.Popen(
                [str(self.venv_python), "-m", "assistant.core.listener"],
                cwd=str(self.planner_dir),
                # Don't hide windows for now to see errors
                # stdout=subprocess.PIPE,
                # stderr=subprocess.PIPE,
                # creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            print("Planner started")
        except Exception as e:
            print(f"Failed to start planner: {e}")
            import traceback
            traceback.print_exc()
    
    def stop_planner(self):
        """Stop the planner listener."""
        if self.planner_process:
            self.planner_process.terminate()
            self.planner_process = None
            print("Planner stopped")
    
    def start_wake(self):
        """Start the wake listener."""
        if self.wake_process and self.wake_process.poll() is None:
            print("Wake listener is already running")
            return
        
        print(f"Starting wake listener from {self.planner_dir}...")
        print(f"Python path: {self.venv_python}")
        print(f"Python exists: {self.venv_python.exists()}")
        
        try:
            self.wake_process = subprocess.Popen(
                [str(self.venv_python), "-m", "assistant.core.wake"],
                cwd=str(self.planner_dir),
                # Don't hide windows for now to see errors
                # stdout=subprocess.PIPE,
                # stderr=subprocess.PIPE,
                # creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            print("Wake listener started")
        except Exception as e:
            print(f"Failed to start wake listener: {e}")
            import traceback
            traceback.print_exc()
    
    def stop_wake(self):
        """Stop the wake listener."""
        if self.wake_process:
            self.wake_process.terminate()
            self.wake_process = None
            print("Wake listener stopped")
    
    def start_dashboard(self):
        """Start the dashboard backend."""
        if self.dashboard_process and self.dashboard_process.poll() is None:
            print("Dashboard is already running")
            return
        
        print(f"Starting dashboard from {self.planner_dir}...")
        print(f"Python path: {self.venv_python}")
        print(f"Python exists: {self.venv_python.exists()}")
        
        try:
            self.dashboard_process = subprocess.Popen(
                [str(self.venv_python), "-m", "assistant.dashboard.main"],
                cwd=str(self.planner_dir),
                # Don't hide windows for now to see errors
            )
            print("Dashboard started")
        except Exception as e:
            print(f"Failed to start dashboard: {e}")
            import traceback
            traceback.print_exc()
    
    def stop_dashboard(self):
        """Stop the dashboard backend."""
        if self.dashboard_process:
            self.dashboard_process.terminate()
            self.dashboard_process = None
            print("Dashboard stopped")
    
    def start_all(self):
        """Start all Aether components."""
        self.start_ollama()
        time.sleep(2)  # Wait for Ollama to start
        self.start_planner()
        time.sleep(1)  # Wait for planner to start
        self.start_wake()
        # Optionally start dashboard
        # self.start_dashboard()
    
    def stop_all(self):
        """Stop all Aether components."""
        self.stop_wake()
        self.stop_planner()
        self.stop_dashboard()
        self.stop_ollama()
    
    def open_dashboard(self):
        """Open the Aether dashboard in browser."""
        import webbrowser
        import time
        
        # Check if dashboard is running
        if not (self.dashboard_process and self.dashboard_process.poll() is None):
            print("Starting dashboard...")
            self.start_dashboard()
            time.sleep(2)  # Wait for dashboard to start
        
        # Open dashboard in browser with cache-busting
        webbrowser.open("http://localhost:8001?t=" + str(int(time.time())))
    
    def get_status(self) -> str:
        """Get current status of all components."""
        status = []
        
        # Check Ollama
        try:
            import urllib.request
            req = urllib.request.Request("http://127.0.0.1:11434/api/tags", timeout=1)
            with urllib.request.urlopen(req):
                status.append("Ollama: Running")
        except:
            status.append("Ollama: Stopped")
        
        # Check Planner
        if self.planner_process and self.planner_process.poll() is None:
            status.append("Planner: Running")
        else:
            status.append("Planner: Stopped")
        
        # Check Wake
        if self.wake_process and self.wake_process.poll() is None:
            status.append("Wake: Running")
        else:
            status.append("Wake: Stopped")
        
        # Check Dashboard
        if self.dashboard_process and self.dashboard_process.poll() is None:
            status.append("Dashboard: Running")
        else:
            status.append("Dashboard: Stopped")
        
        return "\n".join(status)
    
    def enable_autostart(self):
        """Enable auto-start on boot."""
        if os.name != 'nt':
            print("Auto-start only supported on Windows")
            return
        
        import winreg
        
        exe_path = sys.executable
        script_path = str(Path(__file__).parent / "tray_app.py")
        
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, "Aether", 0, winreg.REG_SZ, f'"{exe_path}" "{script_path}"')
            winreg.CloseKey(key)
            print("Auto-start enabled")
        except Exception as e:
            print(f"Failed to enable auto-start: {e}")
    
    def disable_autostart(self):
        """Disable auto-start on boot."""
        if os.name != 'nt':
            print("Auto-start only supported on Windows")
            return
        
        import winreg
        
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
            winreg.DeleteValue(key, "Aether")
            winreg.CloseKey(key)
            print("Auto-start disabled")
        except Exception as e:
            print(f"Failed to disable auto-start: {e}")
    
    def quit(self):
        """Quit the tray application."""
        self.running = False
        self.stop_all()
        print("Exiting Aether...")
    
    def run(self):
        """Run the system tray application."""
        if not PYSTRAY_AVAILABLE:
            print("pystray not available. Please install with: pip install pystray pillow")
            return
        
        icon = pystray.Icon(
            "Aether",
            self.create_icon(),
            "Aether AI Assistant",
            menu=pystray.Menu(
                pystray.MenuItem("Start All", lambda _: self.start_all()),
                pystray.MenuItem("Stop All", lambda _: self.stop_all()),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Start Planner", lambda _: self.start_planner()),
                pystray.MenuItem("Stop Planner", lambda _: self.stop_planner()),
                pystray.MenuItem("Start Wake Listener", lambda _: self.start_wake()),
                pystray.MenuItem("Stop Wake Listener", lambda _: self.stop_wake()),
                pystray.MenuItem("Start Dashboard", lambda _: self.start_dashboard()),
                pystray.MenuItem("Stop Dashboard", lambda _: self.stop_dashboard()),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Open Dashboard", lambda _: self.open_dashboard()),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Enable Auto-start", lambda _: self.enable_autostart()),
                pystray.MenuItem("Disable Auto-start", lambda _: self.disable_autostart()),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Status", lambda _: print(self.get_status())),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Quit", lambda _: self.quit()),
            )
        )
        
        print("Aether system tray started")
        icon.run()


def main():
    """Main entry point."""
    app = AetherTrayApp()
    
    # Try to start all components automatically
    print("Starting Aether components...")
    app.start_all()
    
    # Run the tray icon
    app.run()


if __name__ == "__main__":
    main()
