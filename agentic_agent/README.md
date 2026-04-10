# Agentic Agent

An AI agent for desktop and Chrome browser automation powered by local LLM (Ollama).

## Features

- **Browser Automation**: Chrome automation using Playwright with CDP
- **Desktop Automation**: GUI automation using PyAutoGUI
- **File Management**: Read, write, copy, move, delete files
- **LLM-Powered**: Natural language task understanding with Ollama
- **OpenHands Integration**: Package as OpenHands skill

## Installation

```bash
# Install dependencies
pip install -e .

# Install Playwright browsers
playwright install chromium
```

## Usage

```bash
# Run a task
python -m agentic_agent "Open Chrome and go to example.com"

# Interactive mode
python -m agentic_agent --interactive

# Browser commands
python -m agentic_agent browser navigate https://example.com
python -m agentic_agent browser screenshot output.png

# Desktop commands
python -m agentic_agent desktop screenshot
python -m agentic_agent desktop click 100,200

# File commands
python -m agentic_agent file read config.json
python -m agentic_agent file write hello.txt "Hello World"
```

## Configuration

Set Ollama endpoint in environment:
```bash
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=llama3.2
```

## License

MIT