#!/usr/bin/env python3
"""
Aether One-Click Setup Script
Automatically checks system requirements and installs dependencies.
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_success(text):
    print(f"✓ {text}")


def print_error(text):
    print(f"✗ {text}")


def print_warning(text):
    print(f"⚠ {text}")


def check_python():
    """Check if Python 3.11+ is installed."""
    print_header("Checking Python Installation")
    
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} installed")
        return True
    else:
        print_error(f"Python 3.11+ required (found {version.major}.{version.minor})")
        print("Please install Python 3.11+ from https://www.python.org/downloads/")
        return False


def check_ram():
    """Check if system has enough RAM."""
    print_header("Checking System Memory")
    
    if platform.system() == "Windows":
        try:
            import psutil
            ram_gb = psutil.virtual_memory().total / (1024**3)
        except ImportError:
            print_warning("psutil not installed, skipping RAM check")
            return True
    else:
        # Fallback for other OS
        ram_gb = 8  # Assume minimum
    
    if ram_gb >= 8:
        print_success(f"{ram_gb:.1f} GB RAM detected (minimum: 8 GB)")
        return True
    else:
        print_error(f"{ram_gb:.1f} GB RAM detected (minimum: 8 GB)")
        print("Aether requires at least 8 GB RAM for optimal performance")
        return False


def check_disk_space():
    """Check if there's enough disk space."""
    print_header("Checking Disk Space")
    
    try:
        import shutil
        path = Path.cwd()
        free_gb = shutil.disk_usage(path).free / (1024**3)
        
        if free_gb >= 10:
            print_success(f"{free_gb:.1f} GB free space (minimum: 10 GB)")
            return True
        else:
            print_error(f"{free_gb:.1f} GB free space (minimum: 10 GB)")
            print("Aether requires at least 10 GB free space")
            return False
    except Exception as e:
        print_warning(f"Could not check disk space: {e}")
        return True


def check_ollama():
    """Check if Ollama is installed and running."""
    print_header("Checking Ollama")
    
    try:
        import urllib.request
        import json
        
        req = urllib.request.Request("http://127.0.0.1:11434/api/tags", timeout=2)
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())
            print_success(f"Ollama is running with {len(data.get('models', []))} models")
            return True
    except:
        print_warning("Ollama is not running or not installed")
        print("Ollama is required for Aether to function")
        print("Install from: https://ollama.com/download")
        print("After installation, run: ollama serve")
        return False


def install_python_dependencies():
    """Install Python dependencies."""
    print_header("Installing Python Dependencies")
    
    planner_dir = Path("assistant/planner")
    if not planner_dir.exists():
        print_error("Planner directory not found")
        return False
    
    venv_dir = planner_dir / ".venv"
    
    # Create virtual environment if it doesn't exist
    if not venv_dir.exists():
        print("Creating virtual environment...")
        try:
            subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
            print_success("Virtual environment created")
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to create virtual environment: {e}")
            return False
    
    # Install dependencies
    pip_path = venv_dir / "Scripts" / "pip.exe" if platform.system() == "Windows" else venv_dir / "bin" / "pip"
    
    print("Installing dependencies...")
    try:
        subprocess.run([str(pip_path), "install", "-r", "pyproject.toml"], 
                       cwd=planner_dir, check=True)
        print_success("Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        return False


def install_ollama_models():
    """Download required Ollama models."""
    print_header("Downloading Ollama Models")
    
    models = ["qwen2.5:1.5b-instruct", "llama3:8b", "nomic-embed-text"]
    
    for model in models:
        print(f"Downloading {model}...")
        try:
            subprocess.run(["ollama", "pull", model], check=True, timeout=600)
            print_success(f"{model} downloaded")
        except subprocess.TimeoutExpired:
            print_error(f"Timeout downloading {model}")
            return False
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to download {model}: {e}")
            return False
        except FileNotFoundError:
            print_error("Ollama not found in PATH")
            print("Install Ollama from: https://ollama.com/download")
            return False
    
    return True


def create_shortcuts():
    """Create desktop shortcuts for easy access."""
    print_header("Creating Desktop Shortcuts")
    
    if platform.system() != "Windows":
        print_warning("Shortcut creation only supported on Windows")
        return True
    
    desktop = Path.home() / "Desktop"
    
    # Create shortcut for wake listener
    shortcut_content = f"""@echo off
cd /d {Path.cwd()}\\assistant\\planner
.venv\\Scripts\\python.exe -m assistant.core.wake
pause
"""
    
    shortcut_path = desktop / "Aether Wake Listener.bat"
    try:
        with open(shortcut_path, "w") as f:
            f.write(shortcut_content)
        print_success(f"Created shortcut: {shortcut_path}")
    except Exception as e:
        print_error(f"Failed to create shortcut: {e}")
    
    # Create shortcut for planner
    shortcut_content = f"""@echo off
cd /d {Path.cwd()}\\assistant\\planner
.venv\\Scripts\\python.exe -m assistant.core.listener
pause
"""
    
    shortcut_path = desktop / "Aether Planner.bat"
    try:
        with open(shortcut_path, "w") as f:
            f.write(shortcut_content)
        print_success(f"Created shortcut: {shortcut_path}")
    except Exception as e:
        print_error(f"Failed to create shortcut: {e}")
    
    return True


def main():
    """Main setup function."""
    print_header("Aether One-Click Setup")
    print("This script will check your system and install Aether.")
    print()
    
    # Run checks
    checks = [
        check_python(),
        check_ram(),
        check_disk_space(),
        check_ollama(),
    ]
    
    if not all(checks):
        print_header("Setup Failed")
        print("Please fix the errors above and run this script again.")
        return 1
    
    # Install dependencies
    if not install_python_dependencies():
        print_header("Setup Failed")
        return 1
    
    # Download models
    response = input("\nDownload Ollama models? This will take several minutes and ~6GB space. (y/n): ")
    if response.lower() == 'y':
        if not install_ollama_models():
            print_header("Setup Failed")
            return 1
    else:
        print_warning("Skipping model download")
        print("You can download models later by running: ollama pull llama3:8b")
    
    # Create shortcuts
    create_shortcuts()
    
    print_header("Setup Complete!")
    print("\nTo start Aether:")
    print("1. Start Ollama: ollama serve")
    print("2. Start the planner: (double-click 'Aether Planner.bat' on desktop)")
    print("3. Start the wake listener: (double-click 'Aether Wake Listener.bat' on desktop)")
    print("\nOr use hotkey mode:")
    print("1. Set environment: set AETHER_ENABLE_HOTKEY=1")
    print("2. Start wake listener with hotkey enabled")
    print("3. Press Win+Alt+A to activate")
    print("\nFor more information, see: assistant/docs/COMMANDS.md")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
