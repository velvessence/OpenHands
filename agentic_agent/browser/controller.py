"""
Browser Automation Module using Playwright with Chrome DevTools Protocol.

Provides capabilities for:
- Chrome launch with remote debugging
- Page navigation
- Element clicking and form filling
- Screenshot capture
- Page content extraction
"""

import asyncio
import base64
import os
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
except ImportError:
    raise ImportError("playwright not installed. Run: pip install playwright")


@dataclass
class BrowserConfig:
    """Configuration for browser automation."""
    headless: bool = False
    user_data_dir: Optional[str] = None
    viewport_size: Dict[str, int] = None
    remote_debugging_port: int = 9222
    browser_executable_path: Optional[str] = None
    
    def __post_init__(self):
        if self.viewport_size is None:
            self.viewport_size = {"width": 1920, "height": 1080}


class BrowserController:
    """
    Controller for browser automation using Playwright.
    
    Usage:
        controller = BrowserController()
        await controller.start()
        await controller.navigate("https://example.com")
        await controller.screenshot("example.png")
        await controller.stop()
    """
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._is_running = False
    
    async def start(self) -> "BrowserController":
        """Launch browser and create new page."""
        self.playwright = await async_playwright().start()
        
        # Launch Chromium with optional remote debugging
        launch_options = {
            "headless": self.config.headless,
            "args": [
                f"--remote-debugging-port={self.config.remote_debugging_port}",
                "--disable-blink-features=AutomationControlled",
            ]
        }
        
        if self.config.browser_executable_path:
            launch_options["executable_path"] = self.config.browser_executable_path
        
        self.browser = await self.playwright.chromium.launch(**launch_options)
        
        # Create browser context with viewport settings
        self.context = await self.browser.new_context(
            viewport=self.config.viewport_size,
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        )
        
        # Create new page
        self.page = await self.context.new_page()
        self._is_running = True
        
        return self
    
    async def stop(self):
        """Close browser and cleanup."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self._is_running = False
    
    async def navigate(self, url: str, wait_until: str = "networkidle") -> Dict[str, Any]:
        """
        Navigate to a URL.
        
        Args:
            url: Target URL
            wait_until: When to consider navigation complete
            
        Returns:
            Dictionary with page title, URL, and status
        """
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")
        
        response = await self.page.goto(url, wait_until=wait_until)
        
        return {
            "url": self.page.url,
            "title": await self.page.title(),
            "status": response.status if response else None,
        }
    
    async def click(self, selector: str, timeout: float = 5000) -> bool:
        """
        Click an element by CSS selector.
        
        Args:
            selector: CSS selector for the element
            timeout: Timeout in milliseconds
            
        Returns:
            True if click succeeded
        """
        if not self.page:
            raise RuntimeError("Browser not started.")
        
        try:
            await self.page.click(selector, timeout=timeout)
            return True
        except Exception as e:
            return False
    
    async def fill_form(self, form_data: Dict[str, str]) -> bool:
        """
        Fill form fields.
        
        Args:
            form_data: Dictionary mapping CSS selectors to values
            
        Returns:
            True if all fields filled successfully
        """
        if not self.page:
            raise RuntimeError("Browser not started.")
        
        try:
            for selector, value in form_data.items():
                await self.page.fill(selector, value)
            return True
        except Exception as e:
            return False
    
    async def type_text(self, selector: str, text: str, delay: int = 0) -> bool:
        """
        Type text into an element (character by character).
        
        Args:
            selector: CSS selector
            text: Text to type
            delay: Delay between keystrokes in ms
            
        Returns:
            True if typing succeeded
        """
        if not self.page:
            raise RuntimeError("Browser not started.")
        
        try:
            await self.page.type(selector, text, delay=delay)
            return True
        except Exception as e:
            return False
    
    async def get_page_content(self, selector: Optional[str] = None) -> str:
        """
        Get page content.
        
        Args:
            selector: Optional CSS selector to get specific element
            
        Returns:
            Page HTML or element HTML
        """
        if not self.page:
            raise RuntimeError("Browser not started.")
        
        if selector:
            return await self.page.inner_html(selector)
        return await self.page.content()
    
    async def get_text(self, selector: str) -> Optional[str]:
        """Get text content of an element."""
        if not self.page:
            raise RuntimeError("Browser not started.")
        
        try:
            return await self.page.inner_text(selector)
        except Exception:
            return None
    
    async def evaluate(self, script: str) -> Any:
        """Execute JavaScript in page context."""
        if not self.page:
            raise RuntimeError("Browser not started.")
        
        return await self.page.evaluate(script)
    
    async def screenshot(
        self, 
        path: Optional[str] = None, 
        full_page: bool = False
    ) -> str:
        """
        Take a screenshot.
        
        Args:
            path: Optional path to save screenshot. If None, returns base64
            full_page: Whether to capture full scrollable page
            
        Returns:
            Screenshot path if saved, or base64 encoded image data
        """
        if not self.page:
            raise RuntimeError("Browser not started.")
        
        screenshot_bytes = await self.page.screenshot(full_page=full_page)
        
        if path:
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "wb") as f:
                f.write(screenshot_bytes)
            return path
        
        return base64.b64encode(screenshot_bytes).decode()
    
    async def wait_for_selector(
        self, 
        selector: str, 
        timeout: float = 10000,
        state: str = "visible"
    ) -> bool:
        """
        Wait for an element to appear.
        
        Args:
            selector: CSS selector
            timeout: Timeout in ms
            state: Expected state ("visible", "hidden", "attached")
            
        Returns:
            True if element found
        """
        if not self.page:
            raise RuntimeError("Browser not started.")
        
        try:
            await self.page.wait_for_selector(selector, timeout=timeout, state=state)
            return True
        except Exception:
            return False
    
    async def get_all_links(self) -> List[Dict[str, str]]:
        """Get all links on the page."""
        if not self.page:
            raise RuntimeError("Browser not started.")
        
        links = await self.page.evaluate("""
            Array.from(document.querySelectorAll('a')).map(a => ({
                text: a.textContent.trim(),
                href: a.href
            }))
        """)
        return links
    
    async def execute_action(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Execute a browser action based on action name.
        
        Args:
            action: Action name (navigate, click, fill, screenshot, etc.)
            **kwargs: Action-specific arguments
            
        Returns:
            Result dictionary
        """
        actions = {
            "navigate": lambda: self.navigate(kwargs.get("url", "about:blank")),
            "click": lambda: self.click(kwargs.get("selector", "")),
            "fill": lambda: self.fill_form(kwargs.get("form_data", {})),
            "type": lambda: self.type_text(
                kwargs.get("selector", ""), 
                kwargs.get("text", "")
            ),
            "screenshot": lambda: self.screenshot(kwargs.get("path")),
            "content": lambda: self.get_page_content(kwargs.get("selector")),
            "links": lambda: self.get_all_links(),
        }
        
        if action not in actions:
            return {"success": False, "error": f"Unknown action: {action}"}
        
        try:
            result = await actions[action]()
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    @property
    def is_running(self) -> bool:
        """Check if browser is running."""
        return self._is_running
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()


# Convenience function for quick usage
async def quick_screenshot(url: str, path: str, **kwargs) -> str:
    """Quickly navigate to URL and take screenshot."""
    async with BrowserController() as browser:
        await browser.navigate(url)
        return await browser.screenshot(path, **kwargs)


if __name__ == "__main__":
    # Example usage
    async def main():
        async with BrowserController() as browser:
            await browser.navigate("https://example.com")
            await browser.screenshot("example.png")
            print(f"Title: {await browser.page.title()}")
    
    asyncio.run(main())