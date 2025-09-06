# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function

"""
#########################################################
#                                                       #
#  Universal Logger Module                              #
#  Version: 1.0                                         #
#  Created by Lululla (https://github.com/Belfagor2005) #
#  License: CC BY-NC-SA 4.0                             #
#  https://creativecommons.org/licenses/by-nc-sa/4.0    #
#  Last Modified: 2025-05-27                            #
#                                                       #
#  Credits:                                             #
#  - Original concept by Lululla                        #
#  Usage of this code without proper attribution        #
#  is strictly prohibited.                              #
#  For modifications and redistribution,                #
#  please maintain this credit header.                  #
#########################################################
"""

from os import makedirs, remove
from os.path import join, exists
from threading import Lock
from time import strftime


class ColoredLogger:
    LEVELS = {
        "DEBUG": ("\033[92m", "[DEBUG]"),           # green
        "INFO": ("\033[97m", "[INFO] "),            # white
        "WARNING": ("\033[93m", "[WARN] "),         # yellow
        "ERROR": ("\033[91m", "[ERROR]"),           # red
        "CRITICAL": ("\033[95m", "[CRITICAL]"),     # magenta
    }
    END = "\033[0m"
    _instances = {}
    _lock = Lock()

    def __new__(cls, log_path=None, plugin_name="generic", clear_on_start=True, max_size_mb=1):
        """Singleton for log_path + plugin_name combination"""
        instance_key = f"{log_path}_{plugin_name}"

        if instance_key not in cls._instances:
            with cls._lock:
                if instance_key not in cls._instances:
                    instance = super().__new__(cls)
                    cls._instances[instance_key] = instance
                    instance._initialize(log_path, plugin_name, clear_on_start, max_size_mb)

        return cls._instances[instance_key]

    def _initialize(self, log_path, plugin_name, clear_on_start, max_size_mb):
        """Initializing the instance"""
        self.plugin_name = plugin_name
        self.max_size_mb = max_size_mb

        # Determine the path of the log file
        if log_path:
            # Create the directory if it does not exist
            if not exists(log_path):
                try:
                    makedirs(log_path)
                except Exception as e:
                    print(f"Error creating log directory {log_path}: {e}")
                    log_path = None

        if log_path:
            self.log_file = join(log_path, f"{plugin_name}.log")

            if clear_on_start and exists(self.log_file):
                try:
                    remove(self.log_file)
                except Exception as e:
                    print(f"Error removing old log file: {e}")
        else:
            self.log_file = None

        self._initialized = True

    def log(self, level, message):
        """Base logging method"""
        if not hasattr(self, '_initialized'):
            return

        color, label = self.LEVELS.get(level.upper(), ("", "[LOG] "))
        timestamp = strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"{timestamp} {self.plugin_name} {label} {message}"

        # Output colored console
        print(f"{timestamp} {self.plugin_name} {label} {color}{message}{self.END}")

        # Scrittura su file
        if self.log_file:
            self._write_to_file(formatted_message)
            self._check_rotation()

    def _write_to_file(self, message):
        """Secure file writing with timeout"""
        try:
            with open(self.log_file, "a") as f:
                f.write(message + "\n")
                f.flush()
        except Exception as e:
            print(f"[LOG ERROR] Cannot write to {self.log_file}: {e}")

    def _check_rotation(self):
        """Check if you need to rotate the log"""
        try:
            if not exists(self.log_file):
                return

            file_size = self._get_file_size_mb()
            if file_size > self.max_size_mb:
                self._rotate_logs()
        except Exception as e:
            print(f"[LOG ERROR] Rotation check failed: {e}")

    def _get_file_size_mb(self):
        """Returns the file size in MB"""
        try:
            from os.path import getsize
            return getsize(self.log_file) / (1024 * 1024)
        except:
            return 0

    def _rotate_logs(self):
        """Perform log rotation"""
        try:
            import glob
            import os

            base_name = self.log_file
            pattern = f"{base_name}.*"

            # Find all existing backup files
            backups = sorted(glob.glob(pattern), reverse=True)

            # Delete the oldest backups (keep only the last 5)
            for old_backup in backups[4:]:
                try:
                    os.remove(old_backup)
                except:
                    pass

            # Rename existing files
            for i in range(min(len(backups), 4), 0, -1):
                old_name = f"{base_name}.{i}" if i > 1 else base_name
                new_name = f"{base_name}.{i + 1}"

                if exists(old_name):
                    try:
                        os.rename(old_name, new_name)
                    except:
                        pass

        except Exception as e:
            print(f"[LOG ERROR] Log rotation failed: {e}")

    def debug(self, message, *args):
        self.log("DEBUG", message % args if args else message)

    def info(self, message, *args):
        self.log("INFO", message % args if args else message)

    def warning(self, message, *args):
        self.log("WARNING", message % args if args else message)

    def error(self, message, *args):
        self.log("ERROR", message % args if args else message)

    def critical(self, message, *args):
        self.log("CRITICAL", message % args if args else message)

    def exception(self, message, *args):
        """Log an exception with traceback"""
        import sys
        import traceback
        exc_info = sys.exc_info()
        traceback_text = ''.join(traceback.format_exception(*exc_info))
        full_message = f"{message % args if args else message}\n{traceback_text}"
        self.log("ERROR", full_message)

    def show_message(self, session, text, timeout=5):
        """Display a message on the screen (requires session)"""
        try:
            from Screens.MessageBox import MessageBox
            session.openWithCallback(
                self._message_closed,
                MessageBox,
                text=text,
                type=MessageBox.TYPE_INFO,
                timeout=timeout
            )
        except Exception as e:
            self.error("Cannot show message: %s", e)

    def _message_closed(self, ret=None):
        """Callback for closed message"""
        self.debug("MessageBox closed")


def get_logger(log_path=None, plugin_name="generic", clear_on_start=True, max_size_mb=1):
    """
    Factory function to get a logger instance
    Args:
        log_path (str): Path to save the log file
        plugin_name (str): Plugin name (used for file name)
        clear_on_start (bool): Whether to clear the log on startup
        max_size_mb (int): Maximum size in MB before rotation
    Returns:
        ColoredLogger: Logger instance
    """
    return ColoredLogger(
        log_path=log_path,
        plugin_name=plugin_name,
        clear_on_start=clear_on_start,
        max_size_mb=max_size_mb
    )


"""
````markdown
# 🎉 My Universal Logger Plugin

A simple and flexible Python logging utility designed for plugins.
Keep your plugin logs organized, easy to read, and automatically handled!

---

## 🚀 Features

- Custom logger for each plugin
- Automatic log file creation and rotation
- Clear logs on startup (optional)
- Debug, info, warning, error messages
- Full exception tracking
- Display messages directly to users

---

## 🛠 Installation

Simply copy the logger module (`your_logger_module.py`) into your plugin folder.
No extra dependencies needed — just pure Python magic! ✨

---

## 📝 Quick Start

```python
if __name__ == "__main__":
    # Example of module usage
    logger = get_logger(
        log_path="/tmp/my_plugin_logs",
        plugin_name="my_awesome_plugin",
        clear_on_start=True,
        max_size_mb=2
    )

    logger.debug("This is a debug message")
    logger.info("This is an informational message")
    logger.warning("Warning!")
    logger.error("Error!")

    try:
        raise ValueError("Sample error")
    except Exception as e:
        logger.exception("Caught exception: %s", e)
````

---

## 🔧 Using the Logger in Your Plugins

1. **Import the module**

```python
from .UniLogger import get_logger
```

2. **Create a logger instance**

```python
class MyPlugin:
    def __init__(self):
        self.logger = get_logger(
            log_path="/tmp/my_plugin_logs",
            plugin_name="MyPlugin",
            clear_on_start=True,
            max_size_mb=1
        )
```

3. **Log messages in your functions**

```python
def my_function(self):
    self.logger.debug("Starting function")
    self.logger.info("Operation completed")

    try:
        # code that may raise errors
        pass
    except Exception as e:
        self.logger.exception("Error during operation: %s", e)
```

4. **Show messages to users**

```python
def show_info(self, session):
    self.logger.show_message(session, "Operation completed successfully!")
```

---

## 📂 Where Logs Go

Logs are saved in the path you specify (`log_path`).
Each plugin can have its own log folder and file size limit for easy rotation.

---

## ⚡ License

MIT License — free to use and modify!

```
"""
