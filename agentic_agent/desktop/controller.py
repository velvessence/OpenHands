"""
Desktop Automation Module - Simplified version that works without display.

Provides capabilities for:
- Screenshot capture
- File operations
"""

import os
import subprocess
import time
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass


@dataclass
class DesktopConfig:
    """Configuration for desktop automation."""
    screenshot_dir: str = "./screenshots"


class DesktopController:
    """
    Controller for desktop automation.
    
    Usage:
        controller = DesktopController()
        controller.screenshot("desktop.png")
    """
    
    def __init__(self, config: Optional[DesktopConfig] = None):
        self.config = config or DesktopConfig()
        self._screenshot_dir = Path(self.config.screenshot_dir)
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)
        self._pyautogui = None
    
    def _ensure_pyautogui(self):
        """Lazy load pyautogui only when needed."""
        if self._pyautogui is None:
            try:
                import pyautogui
                pyautogui.FAILSAFE = True
                pyautogui.PAUSE = 0.1
                self._pyautogui = pyautogui
            except ImportError:
                return None
        return self._pyautogui
    
    def get_screen_size(self) -> Tuple[int, int]:
        """Get screen resolution."""
        pyautogui = self._ensure_pyautogui()
        if pyautogui:
            return pyautogui.size()
        return (1920, 1080)  # Default
    
    def get_current_mouse_position(self) -> Tuple[int, int]:
        """Get current mouse position."""
        pyautogui = self._ensure_pyautogui()
        if pyautogui:
            return pyautogui.position()
        return (0, 0)
    
    def click_at(self, x: int, y: int, button: str = "left", clicks: int = 1) -> bool:
        """Click at specific coordinates."""
        pyautogui = self._ensure_pyautogui()
        if pyautogui:
            try:
                pyautogui.click(x, y, clicks=clicks, button=button)
                return True
            except Exception:
                return False
        return False
    
    def move_to(self, x: int, y: int, duration: float = 0.5) -> bool:
        """Move mouse to coordinates."""
        pyautogui = self._ensure_pyautogui()
        if pyautogui:
            try:
                pyautogui.moveTo(x, y, duration=duration)
                return True
            except Exception:
                return False
        return False
    
    def scroll(self, clicks: int) -> bool:
        """Scroll the mouse."""
        pyautogui = self._ensure_pyautogui()
        if pyautogui:
            try:
                pyautogui.scroll(clicks)
                return True
            except Exception:
                return False
        return False
    
    def type_text(self, text: str, interval: float = 0.0) -> bool:
        """Type text using keyboard."""
        pyautogui = self._ensure_pyautogui()
        if pyautogui:
            try:
                pyautogui.write(text, interval=interval)
                return True
            except Exception:
                return False
        return False
    
    def press_key(self, key: str) -> bool:
        """Press a single key."""
        pyautogui = self._ensure_pyautogui()
        if pyautogui:
            try:
                pyautogui.press(key)
                return True
            except Exception:
                return False
        return False
    
    def hotkey(self, *keys) -> bool:
        """Press a hotkey combination."""
        pyautogui = self._ensure_pyautogui()
        if pyautogui:
            try:
                pyautogui.hotkey(*keys)
                return True
            except Exception:
                return False
        return False
    
    def screenshot(self, path: Optional[str] = None) -> str:
        """Take a screenshot."""
        if path is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            path = str(self._screenshot_dir / f"screenshot_{timestamp}.png")
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        
        # Try multiple screenshot methods
        # Method 1: pyscreenshot
        try:
            import pyscreenshot
            image = pyscreenshot.grab()
            image.save(path)
            return path
        except Exception:
            pass
        
        # Method 2: mss
        try:
            import mss
            with mss.mss() as sct:
                sct.shot(output=path)
            return path
        except Exception:
            pass
        
        # Method 3: PIL
        try:
            import pyautogui
            image = pyautogui.screenshot()
            image.save(path)
            return path
        except Exception:
            pass
        
        # Method 4: gnome-screenshot (Linux)
        try:
            subprocess.run(["gnome-screenshot", "-f", path], check=True)
            return path
        except Exception:
            pass
        
        raise RuntimeError("No screenshot method available")
    
    def launch_app(self, command: str, shell: bool = True) -> bool:
        """Launch an application."""
        try:
            subprocess.Popen(command, shell=shell)
            return True
        except Exception:
            return False
    
    def open_application(self, app_name: str) -> bool:
        """Open a common application by name."""
        app_commands = {
            "chrome": "google-chrome",
            "firefox": "firefox",
            "vscode": "code",
            "terminal": "gnome-terminal",
        }
        
        command = app_commands.get(app_name.lower())
        if command:
            return self.launch_app(command)
        return False
    
    def execute_action(self, action: str, **kwargs) -> Dict[str, Any]:
        """Execute a desktop action."""
        actions = {
            "click": lambda: self.click_at(kwargs.get("x", 0), kwargs.get("y", 0)),
            "move_to": lambda: self.move_to(kwargs.get("x", 0), kwargs.get("y", 0)),
            "type": lambda: self.type_text(kwargs.get("text", "")),
            "press": lambda: self.press_key(kwargs.get("key", "")),
            "hotkey": lambda: self.hotkey(*kwargs.get("keys", [])),
            "screenshot": lambda: self.screenshot(kwargs.get("path")),
            "scroll": lambda: self.scroll(kwargs.get("clicks", 0)),
            "open": lambda: self.open_application(kwargs.get("app", "")),
            "launch": lambda: self.launch_app(kwargs.get("command", "")),
        }
        
        if action not in actions:
            return {"success": False, "error": f"Unknown action: {action}"}
        
        try:
            result = actions[action]()
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def __repr__(self):
        return f"DesktopController(screen_size={self.get_screen_size()})"


def quick_screenshot(path: str = "screenshot.png") -> str:
    """Quickly take a screenshot."""
    controller = DesktopController()
    return controller.screenshot(path)


if __name__ == "__main__":
    controller = DesktopController()
    print(f"Screen size: {controller.get_screen_size()}")
    print(f"Screenshot saved to: {controller.screenshot()}")