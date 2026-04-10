"""
Agentic Agent CLI - Command-line interface for the agentic agent.

Usage:
    python -m agentic_agent "task description"
    python -m agentic_agent --interactive
    python -m agentic_agent --browser "https://example.com"
    python -m agentic_agent --desktop screenshot
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Optional

from agentic_agent import __version__
from agentic_agent.agent.brain import AgenticBrain, AgentConfig, execute_task
from agentic_agent.browser.controller import BrowserController, BrowserConfig, quick_screenshot
from agentic_agent.desktop.controller import DesktopController, DesktopConfig, quick_screenshot as desktop_screenshot
from agentic_agent.desktop.file_manager import FileManager, FileManagerConfig


def print_result(result: dict, verbose: bool = False):
    """Print execution result."""
    if result.get("success"):
        print(f"✅ Task completed successfully")
        print(f"   Duration: {result.get('duration', 0):.2f}s")
        if verbose:
            print(f"   Actions: {len(result.get('actions', []))}")
        print(f"   Result: {result.get('result', '')}")
    else:
        print(f"❌ Task failed: {result.get('error', 'Unknown error')}")
        print(f"   Duration: {result.get('duration', 0):.2f}s")


async def run_browser_task(args):
    """Run a browser automation task."""
    config = AgentConfig(
        headless_browser=args.headless,
        workspace_dir=args.workspace or ".",
    )
    
    async with AgenticBrain(config) as brain:
        result = await brain.execute_task(args.task)
        print_result(result, verbose=args.verbose)
        return 0 if result.get("success") else 1


async def run_browser_command(args):
    """Run a browser command."""
    config = BrowserConfig(headless=args.headless)
    
    async with BrowserController(config) as browser:
        if args.command == "navigate":
            result = await browser.navigate(args.url)
            print(f"Navigated to: {result['url']}")
            print(f"Title: {result['title']}")
        elif args.command == "screenshot":
            path = await browser.screenshot(args.output or "screenshot.png")
            print(f"Screenshot saved to: {path}")
        elif args.command == "content":
            content = await browser.get_page_content()
            print(content)
        else:
            print(f"Unknown command: {args.command}")
            return 1
    return 0


def run_desktop_command(args):
    """Run a desktop command."""
    config = DesktopConfig(screenshot_dir=args.workspace or "./screenshots")
    controller = DesktopController(config)
    
    if args.command == "screenshot":
        path = controller.screenshot(args.output or "screenshot.png")
        print(f"Screenshot saved to: {path}")
    elif args.command == "click":
        x, y = args.position.split(",")
        controller.click_at(int(x), int(y))
        print(f"Clicked at ({x}, {y})")
    elif args.command == "type":
        controller.type_text(args.text)
        print(f"Typed: {args.text}")
    elif args.command == "press":
        controller.press_key(args.key)
        print(f"Pressed: {args.key}")
    else:
        print(f"Unknown command: {args.command}")
        return 1
    return 0


def run_file_command(args):
    """Run a file command."""
    config = FileManagerConfig(base_dir=args.workspace or ".")
    fm = FileManager(config)
    
    if args.command == "read":
        content = fm.read_file(args.path)
        print(content if content else "(empty or not found)")
    elif args.command == "write":
        success = fm.write_file(args.path, args.content)
        print(f"Written to: {args.path}" if success else "Write failed")
    elif args.command == "list":
        files = fm.list_dir(args.path or ".")
        for f in files:
            print(f)
    elif args.command == "exists":
        exists = fm.exists(args.path)
        print("Yes" if exists else "No")
    else:
        print(f"Unknown command: {args.command}")
        return 1
    return 0


async def interactive_mode(args):
    """Run in interactive mode."""
    print("🤖 Agentic Agent - Interactive Mode")
    print("=" * 50)
    print("Type your task or 'exit' to quit")
    print()
    
    config = AgentConfig(
        headless_browser=args.headless,
        workspace_dir=args.workspace or ".",
    )
    
    async with AgenticBrain(config) as brain:
        while True:
            try:
                task = input("➤ ")
                if not task.strip():
                    continue
                if task.lower() in ("exit", "quit", "q"):
                    break
                
                result = await brain.execute_task(task)
                print_result(result, verbose=True)
                print()
            except KeyboardInterrupt:
                break
            except EOFError:
                break
    
    print("\nGoodbye! 👋")
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Agentic Agent - AI agent for desktop and browser automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m agentic_agent "Take a screenshot of the desktop"
  python -m agentic_agent "Open Chrome and go to example.com"
  python -m agentic_agent --interactive
  python -m agentic_agent browser navigate https://example.com
  python -m agentic_agent desktop click 100,200
  python -m agentic_agent file read config.json
        """
    )
    
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-w", "--workspace", help="Workspace directory")
    
    subparsers = parser.add_subparsers(dest="mode", help="Operating mode")
    
    # Task mode
    task_parser = subparsers.add_parser("task", help="Execute a task")
    task_parser.add_argument("task", help="Task description")
    task_parser.add_argument("--headless", action="store_true", help="Run browser headless")
    
    # Interactive mode
    interactive_parser = subparsers.add_parser("interactive", help="Interactive mode")
    interactive_parser.add_argument("--headless", action="store_true", help="Run browser headless")
    
    # Browser commands
    browser_parser = subparsers.add_parser("browser", help="Browser commands")
    browser_parser.add_argument("command", help="Command (navigate, screenshot, content)")
    browser_parser.add_argument("args", nargs="*", help="Command arguments")
    browser_parser.add_argument("--headless", action="store_true", help="Run browser headless")
    browser_parser.add_argument("-o", "--output", help="Output path for screenshot")
    
    # Desktop commands
    desktop_parser = subparsers.add_parser("desktop", help="Desktop commands")
    desktop_parser.add_argument("command", help="Command (screenshot, click, type, press)")
    desktop_parser.add_argument("args", nargs="*", help="Command arguments")
    
    # File commands
    file_parser = subparsers.add_parser("file", help="File commands")
    file_parser.add_argument("command", help="Command (read, write, list, exists)")
    file_parser.add_argument("args", nargs="*", help="Command arguments")
    
    args = parser.parse_args()
    
    # Default mode: execute task
    if args.mode is None and len(sys.argv) > 1:
        # Treat first arg as task
        task = " ".join(sys.argv[1:])
        args.mode = "task"
        args.task = task
    
    if args.mode == "task" or (args.mode is None and len(sys.argv) > 1):
        return asyncio.run(run_browser_task(args))
    
    elif args.mode == "interactive":
        return asyncio.run(interactive_mode(args))
    
    elif args.mode == "browser":
        # Parse browser args
        if len(args.args) > 0:
            args.command = args.args[0]
            args.url = args.args[1] if len(args.args) > 1 else None
        return asyncio.run(run_browser_command(args))
    
    elif args.mode == "desktop":
        if len(args.args) > 0:
            args.command = args.args[0]
            if args.command == "click" and len(args.args) > 1:
                args.position = args.args[1]
            elif args.command == "type" and len(args.args) > 1:
                args.text = " ".join(args.args[1:])
            elif args.command == "press" and len(args.args) > 1:
                args.key = args.args[1]
        return run_desktop_command(args)
    
    elif args.mode == "file":
        if len(args.args) > 0:
            args.command = args.args[0]
            if args.command == "read" and len(args.args) > 1:
                args.path = args.args[1]
            elif args.command == "write" and len(args.args) > 1:
                args.path = args.args[1]
                args.content = " ".join(args.args[2:]) if len(args.args) > 2 else ""
            elif args.command in ("list", "exists") and len(args.args) > 1:
                args.path = args.args[1]
        return run_file_command(args)
    
    else:
        # Default: show help
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())