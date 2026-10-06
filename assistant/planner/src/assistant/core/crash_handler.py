"""Crash reporting and error logging for Aether.

Logs errors to files and optionally sends crash reports for debugging.
"""

import os
import sys
import traceback
import datetime
from pathlib import Path
from typing import Optional
import json


class CrashHandler:
    """Handles crash reporting and error logging."""
    
    def __init__(self, app_name: str = "Aether"):
        self.app_name = app_name
        self.log_dir = Path.home() / f".{app_name.lower()}" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.crash_log = self.log_dir / "crashes.log"
        self.error_log = self.log_dir / "errors.log"
        
    def log_error(self, error: Exception, context: Optional[dict] = None) -> str:
        """Log an error to the error log file.
        
        Args:
            error: The exception that occurred
            context: Additional context information
            
        Returns:
            The log entry ID
        """
        timestamp = datetime.datetime.now().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "context": context or {}
        }
        
        # Write to error log
        with open(self.error_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
        
        # Also write human-readable version
        error_id = f"{timestamp.replace(':', '-').replace('.', '-')}"
        readable_log = self.log_dir / f"error_{error_id}.txt"
        with open(readable_log, "w", encoding="utf-8") as f:
            f.write(f"Error Report: {self.app_name}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Error Type: {type(error).__name__}\n")
            f.write(f"Error Message: {str(error)}\n")
            f.write(f"\nContext:\n")
            for key, value in (context or {}).items():
                f.write(f"  {key}: {value}\n")
            f.write(f"\nTraceback:\n")
            f.write(traceback.format_exc())
        
        return error_id
    
    def log_crash(self, exc_type, exc_value, exc_traceback, context: Optional[dict] = None) -> str:
        """Log a crash to the crash log file.
        
        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
            context: Additional context information
            
        Returns:
            The crash ID
        """
        timestamp = datetime.datetime.now().isoformat()
        crash_entry = {
            "timestamp": timestamp,
            "crash_type": exc_type.__name__,
            "crash_message": str(exc_value),
            "traceback": "".join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
            "context": context or {}
        }
        
        # Write to crash log
        with open(self.crash_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(crash_entry) + "\n")
        
        # Write human-readable version
        crash_id = f"crash_{timestamp.replace(':', '-').replace('.', '-')}"
        readable_log = self.log_dir / f"{crash_id}.txt"
        with open(readable_log, "w", encoding="utf-8") as f:
            f.write(f"CRASH REPORT: {self.app_name}\n")
            f.write(f"=" * 50 + "\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Crash Type: {exc_type.__name__}\n")
            f.write(f"Crash Message: {str(exc_value)}\n")
            f.write(f"\nContext:\n")
            for key, value in (context or {}).items():
                f.write(f"  {key}: {value}\n")
            f.write(f"\nFull Traceback:\n")
            f.write("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
        
        return crash_id
    
    def get_recent_errors(self, limit: int = 10) -> list:
        """Get recent error log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of error entries
        """
        if not self.error_log.exists():
            return []
        
        errors = []
        with open(self.error_log, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    errors.append(json.loads(line.strip()))
                except:
                    pass
        
        return errors[-limit:]
    
    def get_recent_crashes(self, limit: int = 10) -> list:
        """Get recent crash log entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of crash entries
        """
        if not self.crash_log.exists():
            return []
        
        crashes = []
        with open(self.crash_log, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    crashes.append(json.loads(line.strip()))
                except:
                    pass
        
        return crashes[-limit:]
    
    def clear_old_logs(self, days: int = 30):
        """Clear log files older than specified days.
        
        Args:
            days: Keep logs newer than this many days
        """
        cutoff = datetime.datetime.now() - datetime.timedelta(days=days)
        
        for log_file in self.log_dir.glob("*.txt"):
            if log_file.stat().st_mtime < cutoff.timestamp():
                log_file.unlink()
        
        # Also clear the main log files if they're too old
        for log_file in [self.crash_log, self.error_log]:
            if log_file.exists() and log_file.stat().st_mtime < cutoff.timestamp():
                log_file.unlink()


def setup_global_crash_handler(app_name: str = "Aether"):
    """Set up global exception handler for the application.
    
    Args:
        app_name: Name of the application
    """
    handler = CrashHandler(app_name)
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        # Log the crash
        crash_id = handler.log_crash(exc_type, exc_value, exc_traceback)
        
        # Print to console
        print(f"\n{'=' * 50}")
        print(f"CRASH DETECTED: {app_name}")
        print(f"{'=' * 50}")
        print(f"Crash ID: {crash_id}")
        print(f"Type: {exc_type.__name__}")
        print(f"Message: {str(exc_value)}")
        print(f"\nA crash report has been saved to:")
        print(f"  {handler.log_dir / f'{crash_id}.txt'}")
        print(f"\nPlease report this issue if it persists.")
        print(f"{'=' * 50}\n")
        
        # Call the default handler
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    # Set the global exception handler
    sys.excepthook = handle_exception
    
    return handler


# Convenience function for logging errors
def log_error(error: Exception, context: Optional[dict] = None) -> str:
    """Convenience function to log an error.
    
    Args:
        error: The exception that occurred
        context: Additional context information
        
    Returns:
        The error ID
    """
    handler = CrashHandler()
    return handler.log_error(error, context)
