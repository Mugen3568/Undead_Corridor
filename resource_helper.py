"""
Resource path helper for PyInstaller compatibility.

This module provides a helper function to correctly resolve file paths
both during development and when the application is bundled as an executable.
"""

import sys
import os


def resource_path(relative_path):
    """
    Get the absolute path to a resource file for read-only assets.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_persistent_path(filename):
    """
    Get a persistent path for writable files (database, config).
    When frozen (exe), this will be in the same folder as the .exe.
    """
    if getattr(sys, 'frozen', False):
        # Path where the .exe is located
        base_path = os.path.dirname(sys.executable)
    else:
        # Path where the script is located
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)
