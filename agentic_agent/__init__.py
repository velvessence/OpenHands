"""Agentic Agent - Desktop and Browser Automation"""

__version__ = "0.1.0"

from agentic_agent.agent.brain import AgenticBrain
from agentic_agent.desktop.controller import DesktopController
from agentic_agent.browser.controller import BrowserController

__all__ = [
    "AgenticBrain",
    "DesktopController", 
    "BrowserController",
]