"""
OpenHands Skill for Browser Automation.

This skill provides browser automation capabilities to OpenHands agents.
"""

import asyncio
import json
from typing import Dict, Any, Optional

from agentic_agent.browser.controller import BrowserController, BrowserConfig
from agentic_agent.agent.brain import AgenticBrain, AgentConfig


class BrowserSkill:
    """
    OpenHands skill for browser automation.
    
    Usage in OpenHands:
        /browser:task "Open Chrome and search for weather"
        /browser:navigate "https://google.com"
        /browser:screenshot "output.png"
    """
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
    
    async def initialize(self):
        """Initialize the browser controller."""
        config = BrowserConfig(headless=self.headless)
        self.browser = BrowserController(config)
        await self.browser.start()
        return self
    
    async def cleanup(self):
        """Cleanup browser resources."""
        if self.browser:
            await self.browser.stop()
    
    async def execute_task(self, task: str) -> Dict[str, Any]:
        """
        Execute a browser task.
        
        Args:
            task: Task description
            
        Returns:
            Result dictionary
        """
        if not self.browser:
            await self.initialize()
        
        # Parse the task and execute actions
        # This is a simplified version - the full version would use LLM
        task_lower = task.lower()
        
        if "navigate" in task_lower or "go to" in task_lower or "open" in task_lower:
            # Extract URL
            import re
            urls = re.findall(r'https?://[^\s]+', task)
            if urls:
                result = await self.browser.navigate(urls[0])
                return {"success": True, "action": "navigate", "result": result}
        
        if "screenshot" in task_lower or "screenshot" in task_lower:
            path = "screenshot.png"
            # Try to extract path from task
            import re
            paths = re.findall(r'["\']([^"\']+\.png|[^"\']+\.jpg)["\']', task)
            if paths:
                path = paths[0]
            result = await self.browser.screenshot(path)
            return {"success": True, "action": "screenshot", "result": result}
        
        if "click" in task_lower:
            import re
            selectors = re.findall(r'["\#\.\w]+[\.#\w]*', task)
            if selectors:
                result = await self.browser.click(selectors[0])
                return {"success": result, "action": "click", "selector": selectors[0]}
        
        return {"success": False, "error": "Could not parse task"}
    
    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL."""
        if not self.browser:
            await self.initialize()
        result = await self.browser.navigate(url)
        return {"success": True, "result": result}
    
    async def screenshot(self, path: str = "screenshot.png") -> Dict[str, Any]:
        """Take a screenshot."""
        if not self.browser:
            await self.initialize()
        result = await self.browser.screenshot(path)
        return {"success": True, "result": result}
    
    async def click(self, selector: str) -> Dict[str, Any]:
        """Click an element."""
        if not self.browser:
            await self.initialize()
        result = await self.browser.click(selector)
        return {"success": result, "result": {"selector": selector}}
    
    async def fill(self, form_data: Dict[str, str]) -> Dict[str, Any]:
        """Fill form fields."""
        if not self.browser:
            await self.initialize()
        result = await self.browser.fill_form(form_data)
        return {"success": result, "result": form_data}


# Skill entry point
_skill_instance: Optional[BrowserSkill] = None


def get_skill():
    """Get or create the skill instance."""
    global _skill_instance
    if _skill_instance is None:
        _skill_instance = BrowserSkill()
    return _skill_instance


async def execute_command(command: str, args: str) -> Dict[str, Any]:
    """
    Execute a skill command.
    
    Args:
        command: Command name
        args: Command arguments
        
    Returns:
        Result dictionary
    """
    skill = get_skill()
    
    commands = {
        "browser:task": skill.execute_task,
        "browser:navigate": lambda a: skill.navigate(a),
        "browser:screenshot": lambda a: skill.screenshot(a),
        "browser:click": lambda a: skill.click(a),
        "browser:fill": lambda a: skill.fill(json.loads(a)),
    }
    
    if command in commands:
        return await commands[command](args)
    
    return {"success": False, "error": f"Unknown command: {command}"}


# For direct execution
if __name__ == "__main__":
    async def main():
        skill = BrowserSkill()
        await skill.initialize()
        
        # Test navigation
        result = await skill.navigate("https://example.com")
        print(f"Navigate: {result}")
        
        # Test screenshot
        result = await skill.screenshot("test.png")
        print(f"Screenshot: {result}")
        
        await skill.cleanup()
    
    asyncio.run(main())