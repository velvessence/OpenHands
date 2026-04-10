"""
LLM-Powered Reasoning Agent using LangChain with Ollama.

Provides:
- Natural language task understanding
- Action planning and execution
- Tool orchestration from browser and desktop modules
"""

import os
import json
import asyncio
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime

# LangChain imports
try:
    from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.tools import Tool
    from langchain_ollama import ChatOllama
except ImportError:
    raise ImportError("langchain or langchain-ollama not installed. Run: pip install langchain langchain-ollama")

from agentic_agent.browser.controller import BrowserController, BrowserConfig
from agentic_agent.desktop.controller import DesktopController, DesktopConfig
from agentic_agent.desktop.file_manager import FileManager, FileManagerConfig


@dataclass
class AgentConfig:
    """Configuration for the agent brain."""
    # Ollama settings
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    
    # Agent settings
    max_iterations: int = 10
    max_execution_time: float = 300.0  # 5 minutes
    verbose: bool = True
    
    # Runtime settings
    headless_browser: bool = True
    workspace_dir: str = "."


SYSTEM_PROMPT = """You are an AI agent that can perform tasks on desktop and in browser.

Available tools:
- browser_navigate: Navigate to a URL in browser
- browser_click: Click an element by CSS selector
- browser_fill: Fill form fields (pass JSON like {"#selector": "value"})
- browser_screenshot: Take a browser screenshot (pass path)
- browser_content: Get page content
- desktop_click: Click at coordinates (pass "x,y")
- desktop_screenshot: Take a desktop screenshot (pass path)
- desktop_type: Type text
- desktop_press: Press a key (enter, esc, etc)
- desktop_hotkey: Press hotkey (comma-separated keys like "ctrl,c")
- file_read: Read file contents
- file_write: Write to file (pass "path,content")
- file_list: List directory files

Parse the user's task and respond with the tool to call and arguments.
Respond in JSON format:
{"tool": "tool_name", "arguments": "arg1,arg2"}

If no tool is needed, respond:
{"tool": "none", "arguments": ""}"""


@dataclass
class Action:
    """Represents a single action to be executed."""
    tool: str
    action: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "action": self.action,
            "parameters": self.parameters,
            "description": self.description,
        }


class AgenticBrain:
    """
    LLM-powered agent brain for task execution.
    
    Uses LangChain with Ollama to understand natural language tasks
    and execute them using browser and desktop automation tools.
    
    Usage:
        brain = AgenticBrain()
        result = await brain.execute_task("Open Chrome and search for AI news")
        print(result)
    """
    
    def __init__(self, config: Optional[AgentConfig] = None):
        self.config = config or AgentConfig()
        
        # Initialize controllers
        self.browser = None
        self.desktop = None
        self.file_manager = None
        
        # LLM will be initialized lazily
        self.llm = None
        self.tools = []
        
        # State
        self._is_initialized = False
        self._action_history: List[Action] = []
    
    def _init_llm(self):
        """Initialize the Ollama LLM."""
        if self.llm is None:
            self.llm = ChatOllama(
                base_url=self.config.ollama_base_url,
                model=self.config.ollama_model,
                temperature=0.7,
            )
        return self.llm
    
    async def _init_browser(self):
        """Initialize browser controller."""
        if self.browser is None:
            browser_config = BrowserConfig(
                headless=self.config.headless_browser,
            )
            self.browser = BrowserController(browser_config)
            await self.browser.start()
    
    def _init_desktop(self):
        """Initialize desktop controller."""
        if self.desktop is None:
            desktop_config = DesktopConfig(
                screenshot_dir=os.path.join(self.config.workspace_dir, "screenshots"),
            )
            self.desktop = DesktopController(desktop_config)
        
        if self.file_manager is None:
            self.file_manager = FileManager(FileManagerConfig(
                base_dir=self.config.workspace_dir,
            ))
    
    async def _init_controllers(self):
        """Initialize all controllers."""
        await self._init_browser()
        self._init_desktop()
        self._is_initialized = True
    
    def _get_available_tools(self) -> List[Tool]:
        """Get list of available tools for the agent."""
        tools = []
        
        # Browser tools
        if self.browser:
            tools.append(Tool(
                name="browser_navigate",
                func=lambda url: asyncio.run(self.browser.navigate(url)),
                description="Navigate to a URL in the browser"
            ))
            tools.append(Tool(
                name="browser_screenshot",
                func=lambda path: asyncio.run(self.browser.screenshot(path)),
                description="Take a screenshot in the browser"
            ))
            tools.append(Tool(
                name="browser_click",
                func=lambda selector: asyncio.run(self.browser.click(selector)),
                description="Click an element by CSS selector"
            ))
            tools.append(Tool(
                name="browser_fill",
                func=lambda data: asyncio.run(self.browser.fill_form(json.loads(data))),
                description="Fill form fields"
            ))
            tools.append(Tool(
                name="browser_content",
                func=lambda sel: asyncio.run(self.browser.get_page_content(sel)),
                description="Get page content"
            ))
        
        # Desktop tools
        if self.desktop:
            tools.append(Tool(
                name="desktop_click",
                func=lambda xy: self._parse_click(xy),
                description="Click at coordinates (x,y)"
            ))
            tools.append(Tool(
                name="desktop_screenshot",
                func=lambda path: self.desktop.screenshot(path),
                description="Take desktop screenshot"
            ))
            tools.append(Tool(
                name="desktop_type",
                func=lambda text: self.desktop.type_text(text),
                description="Type text"
            ))
            tools.append(Tool(
                name="desktop_press",
                func=lambda key: self.desktop.press_key(key),
                description="Press a key"
            ))
            tools.append(Tool(
                name="desktop_hotkey",
                func=lambda keys: self.desktop.hotkey(*keys.split(",")),
                description="Press hotkey combination"
            ))
        
        # File manager tools
        if self.file_manager:
            tools.append(Tool(
                name="file_read",
                func=lambda path: self.file_manager.read_file(path),
                description="Read file contents"
            ))
            tools.append(Tool(
                name="file_write",
                func=lambda args: self._parse_write(args),
                description="Write to file (path,content)"
            ))
            tools.append(Tool(
                name="file_list",
                func=lambda path: self.file_manager.list_dir(path or "."),
                description="List directory"
            ))
            tools.append(Tool(
                name="file_exists",
                func=lambda path: self.file_manager.exists(path),
                description="Check if file exists"
            ))
        
        self.tools = tools
        return tools
    
    def _parse_click(self, xy: str) -> bool:
        """Parse x,y string and click."""
        parts = xy.split(",")
        if len(parts) == 2:
            return self.desktop.click_at(int(parts[0]), int(parts[1]))
        return False
    
    def _parse_write(self, args: str) -> bool:
        """Parse path,content string."""
        # Find first comma
        idx = args.find(",")
        if idx > 0:
            path = args[:idx]
            content = args[idx+1:]
            return self.file_manager.write_file(path, content)
        return False
    
    def _parse_llm_response(self, response: str) -> Optional[Dict[str, str]]:
        """Parse LLM response to extract tool and arguments."""
        # Try to extract JSON from response
        try:
            # Find JSON block
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                data = json.loads(json_match.group())
                return {
                    "tool": data.get("tool", ""),
                    "arguments": data.get("arguments", "")
                }
        except:
            pass
        
        # Try to parse simple format
        try:
            lines = response.strip().split("\n")
            for line in lines:
                if "tool" in line.lower():
                    # Extract tool name
                    tool_match = re.search(r'tool["\s:]+([a-z_]+)', line, re.IGNORECASE)
                    arg_match = re.search(r'arguments?["\s:]+([a-z_,\.]+)', line, re.IGNORECASE)
                    if tool_match:
                        return {
                            "tool": tool_match.group(1),
                            "arguments": arg_match.group(1) if arg_match else ""
                        }
        except:
            pass
        
        return None
    
    async def _execute_tool(self, tool_name: str, arguments: str) -> Dict[str, Any]:
        """Execute a tool with given arguments."""
        tool_map = {
            "browser_navigate": lambda a: asyncio.run(self.browser.navigate(a)),
            "browser_screenshot": lambda a: asyncio.run(self.browser.screenshot(a)),
            "browser_click": lambda a: asyncio.run(self.browser.click(a)),
            "browser_fill": lambda a: asyncio.run(self.browser.fill_form(json.loads(a))),
            "browser_content": lambda a: asyncio.run(self.browser.get_page_content(a)),
            "desktop_click": lambda a: self._parse_click(a),
            "desktop_screenshot": lambda a: self.desktop.screenshot(a),
            "desktop_type": lambda a: self.desktop.type_text(a),
            "desktop_press": lambda a: self.desktop.press_key(a),
            "desktop_hotkey": lambda a: self.desktop.hotkey(*a.split(",")),
            "file_read": lambda a: self.file_manager.read_file(a),
            "file_write": lambda a: self._parse_write(a),
            "file_list": lambda a: self.file_manager.list_dir(a or "."),
            "file_exists": lambda a: self.file_manager.exists(a),
        }
        
        if tool_name not in tool_map:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        try:
            result = tool_map[tool_name](arguments)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def execute_task(self, task: str) -> Dict[str, Any]:
        """
        Execute a task given in natural language.
        
        Args:
            task: Task description in natural language
            
        Returns:
            Dictionary with execution results
        """
        start_time = datetime.now()
        
        # Initialize controllers if not done
        if not self._is_initialized:
            await self._init_controllers()
        
        # Get tools
        if not self.tools:
            self._get_available_tools()
        
        llm = self._init_llm()
        
        # Create prompt
        prompt = f"""{SYSTEM_PROMPT}

User task: {task}

What tool should be used? Respond with JSON."""
        
        # Call LLM
        try:
            response = llm.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Parse response
            parsed = self._parse_llm_response(response_text)
            
            if parsed and parsed.get("tool") and parsed.get("tool") != "none":
                tool_name = parsed["tool"]
                arguments = parsed["arguments"]
                
                # Execute tool
                result = await self._execute_tool(tool_name, arguments)
                
                return {
                    "success": result.get("success", False),
                    "task": task,
                    "tool_used": tool_name,
                    "arguments": arguments,
                    "result": result,
                    "llm_response": response_text,
                    "duration": (datetime.now() - start_time).total_seconds(),
                }
            else:
                return {
                    "success": False,
                    "task": task,
                    "error": "Could not parse task to tool",
                    "llm_response": response_text,
                    "duration": (datetime.now() - start_time).total_seconds(),
                }
        except Exception as e:
            return {
                "success": False,
                "task": task,
                "error": str(e),
                "duration": (datetime.now() - start_time).total_seconds(),
            }
    
    async def close(self):
        """Cleanup resources."""
        if self.browser:
            await self.browser.stop()
        self._is_initialized = False
    
    @property
    def is_initialized(self) -> bool:
        """Check if agent is initialized."""
        return self._is_initialized
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._init_controllers()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Convenience function for quick task execution
async def execute_task(task: str, **kwargs) -> Dict[str, Any]:
    """
    Quickly execute a task.
    
    Usage:
        result = await execute_task("Open Chrome and go to example.com")
    """
    config = AgentConfig(**kwargs)
    async with AgenticBrain(config) as brain:
        return await brain.execute_task(task)


if __name__ == "__main__":
    # Example usage
    async def main():
        async with AgenticBrain() as brain:
            result = await brain.execute_task("Take a screenshot of the desktop")
            print(json.dumps(result, indent=2))
    
    asyncio.run(main())