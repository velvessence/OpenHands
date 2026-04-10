"""Desktop automation module."""

from agentic_agent.desktop.controller import DesktopController, DesktopConfig, quick_screenshot
from agentic_agent.desktop.file_manager import FileManager, FileManagerConfig

__all__ = [
    "DesktopController", 
    "DesktopConfig", 
    "quick_screenshot",
    "FileManager",
    "FileManagerConfig",
]