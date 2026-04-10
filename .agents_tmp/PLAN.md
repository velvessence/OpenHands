# 1. OBJECTIVE

Build an agentic AI agent in Python that can autonomously perform tasks on the desktop (file management, app launching, GUI automation, screenshots) and in Chrome browser (web scraping, form filling, navigation, button clicks, screenshots), using a local LLM (via Ollama in Docker) for decision-making and integrated with OpenHands.

# 2. CONTEXT SUMMARY

**Target Environment:**
- Linux desktop environment (with display/X11)
- Chrome browser with DevTools protocol access
- Python 3.x runtime
- Local LLM via Ollama (running in Docker Desktop)

**Key Components:**
- **LLM Integration**: LangChain with Ollama (OpenAI-compatible API) for local LLM decision-making
- **Browser Automation**: Playwright (Python) for Chrome control via CDP (Chrome DevTools Protocol)
- **Desktop Automation**: PyAutoGUI for cross-platform GUI automation, pyscreenshot for screenshots
- **OpenHands Integration**: Expose as an OpenHands skill/plugin for cloud execution

**Dependencies:**
- `playwright` - Chrome automation via DevTools Protocol
- `pyautogui` - Desktop GUI automation (clicks, keyboard)
- `pyscreenshot` / `Pillow` - Screenshot capture
- `langchain` + `langchain-ollama` - LLM orchestration with local models
- `python-dotenv` - Environment variable management
- `httpx` - HTTP client for Ollama API calls

**Local LLM Configuration:**
- Ollama running in Docker Desktop
- Model: `jackrong/qwen3.5-9b-claude-4.6-opus-reasoning-distilled-gguf:Q4_K_M` (GGUF format)
- Default endpoint: `http://localhost:11434` (verify in Docker)
- API format: OpenAI-compatible (`/v1/chat/completions`)

# 3. APPROACH OVERVIEW

**Architecture:** Modular agent with specialized modules for desktop and browser automation, coordinated by an Ollama-powered reasoning engine.

**Why This Approach:**
- **Ollama** provides easy local LLM deployment with OpenAI-compatible API
- **LangChain** with langchain-ollama offers structured prompt templates and tool-calling for agentic behavior
- **Playwright** provides stable Chrome automation via CDP with better reliability than Selenium
- **PyAutoGUI** is the most mature cross-platform GUI automation library
- Integration as an OpenHands skill allows the agent to run in cloud sandboxes with full browser support

**Alternative Considered:**
- Direct httpx calls to Ollama without LangChain (less structured)
- Selenium for browser (less stable, slower)
- PyGetWindow for desktop (Windows-only)

# 4. IMPLEMENTATION STEPS

## Step 1: Project Structure Setup
- **Goal**: Create the project directory structure and initialize Python package
- **Method**: Create `agentic_agent/` directory with submodules: `browser/`, `desktop/`, `agent/`, `skills/`
- **Reference**: Create `pyproject.toml` with all dependencies

## Step 2: Browser Automation Module (Playwright + CDP)
- **Goal**: Build Chrome automation capabilities (navigation, scraping, forms, clicks, screenshots)
- **Method**: 
  - Create `browser/controller.py` wrapping Playwright's CDP connection
  - Implement methods: `navigate(url)`, `click(selector)`, `fill_form(data)`, `screenshot()`, `get_page_content()`
  - Handle Chrome launch with remote-debugging-port for CDP access
- **Reference**: `agentic_agent/browser/controller.py`

## Step 3: Desktop Automation Module (PyAutoGUI)
- **Goal**: Build desktop automation capabilities (app launching, GUI clicks, screenshots, file management)
- **Method**:
  - Create `desktop/controller.py` wrapping PyAutoGUI and subprocess
  - Implement methods: `launch_app(name)`, `click_at(x, y)`, `screenshot()`, `type_text()`, `press_key()`
  - Add `file_manager.py` for file operations (copy, move, delete, read, write)
- **Reference**: `agentic_agent/desktop/controller.py`

## Step 4: LLM-Powered Reasoning Agent (Ollama)
- **Goal**: Create the agent brain that decides actions based on user tasks using local Ollama
- **Method**:
  - Create `agent/brain.py` using LangChain with Ollama integration
  - Configure Ollama endpoint (default: `http://localhost:11434`)
  - Use model: `jackrong/qwen3.5-9b-claude-4.6-opus-reasoning-distilled-gguf:Q4_K_M`
  - Define structured tools/actions from browser and desktop modules
  - Implement `execute_task(user_prompt)` method that:
    1. Receives natural language task
    2. Plans action sequence using local Ollama LLM
    3. Executes actions via modules
    4. Returns results
- **Reference**: `agentic_agent/agent/brain.py`

## Step 5: OpenHands Skill Integration
- **Goal**: Package as an OpenHands skill for cloud execution
- **Method**:
  - Create `skill.yaml` defining skill metadata and commands
  - Create `__init__.py` with skill entry point
  - Define skill commands: `/browser:task`, `/desktop:task`, `/agent:execute`
- **Reference**: `agentic_agent/skills/browser_skill/`

## Step 6: Main Entry Point & CLI
- **Goal**: Provide user-facing CLI to interact with the agent
- **Method**:
  - Create `main.py` with argparse for CLI commands
  - Support: `python -m agentic_agent "task description"` 
  - Add interactive mode with while loop for continuous commands
- **Reference**: `agentic_agent/main.py`

# 5. TESTING AND VALIDATION

**Browser Automation Tests:**
- Launch Chrome and navigate to a test page → Verify page loads
- Fill a sample form and submit → Verify form data captured
- Click a button and verify navigation → Verify click action works
- Take screenshot → Verify image saved

**Desktop Automation Tests:**
- Launch a test application → Verify app opens
- Perform click at coordinates → Verify click registered
- Take desktop screenshot → Verify screenshot captured
- Create/read/delete a file → Verify file operations work

**Integration Tests:**
- Send "Open Chrome and search for X" task → Verify agent plans and executes correctly
- Send "Take screenshot of desktop" task → Verify result returned
- Test error handling for invalid actions → Verify graceful failure

**Validation Criteria:**
- [ ] Browser module can control Chrome (navigate, click, fill, screenshot)
- [ ] Desktop module can perform GUI actions and file management
- [ ] Agent brain can receive tasks and execute appropriate actions
- [ ] Skill is properly structured for OpenHands integration
- [ ] CLI provides usable interface for testing
