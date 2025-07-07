# Cursor Workspace State

**Last Updated**: 2025-07-07 14:11 UTC

## Workspace Information
- **Absolute Path**: `/workspace`
- **Operating System**: Linux 6.8.0-1024-aws
- **Shell**: `/usr/bin/bash`

## Project Overview
**Project Name**: Modern Autonomous Agent System  
**Description**: A production-ready, deterministic AI agent system with advanced features including state management, plugin architecture, multi-type memory systems, intelligent planning, and self-monitoring capabilities.

### Key Features
- 🎯 Deterministic State Machine with explicit state transitions
- 🧩 Plugin Architecture for extensible actions
- 🧠 Advanced Memory Systems (Working, Episodic, Semantic, Procedural)
- 📋 Intelligent Planning with dependency graphs
- ⚡ Concurrent Execution capabilities
- 🛡️ Robust Error Handling and self-recovery
- 📊 Self-Monitoring with health checks and metrics

## Repository Structure
```
/workspace/
├── .git/                       # Git repository
├── .gitignore                  # Git ignore file (2 lines)
├── README.md                   # Project documentation (13KB, 364 lines)
├── AGENT_UPGRADE_GUIDE.md      # Upgrade documentation (10KB, 331 lines)
├── requirements.txt            # Python dependencies (564B, 30 lines)
├── modern_agent_system.py      # Core agent implementation (25KB, 738 lines)
├── example_plugins.py          # Example action plugins (24KB, 602 lines)
├── modern_agent_demo.py        # Streamlit demo app (13KB, 395 lines)
├── test_modern_agent.py        # Test suite (5.8KB, 194 lines)
├── agent_coffee.py             # Coffee agent implementation (5.6KB, 187 lines)
├── agent_coffee-mlx.py         # MLX variant of coffee agent (6.1KB, 201 lines)
└── AgentCoffee.py              # Another coffee agent variant (11KB, 355 lines)
```

## Dependencies
### Core Dependencies
- openai>=1.3.0
- pydantic>=2.0.0
- redis>=4.5.0
- aiohttp>=3.8.0
- tenacity>=8.2.0
- networkx>=3.0

### Optional Dependencies
- numpy>=1.24.0
- pandas>=2.0.0
- scikit-learn>=1.2.0
- plotly>=5.14.0
- streamlit>=1.25.0
- mlx-lm>=0.0.6

### Development Dependencies
- pytest>=7.3.0
- pytest-asyncio>=0.21.0
- black>=23.0.0
- flake8>=6.0.0
- mypy>=1.3.0

## Git Status
- **Repository State**: Clean (no uncommitted changes)
- **Ignored Files**: 
  - `.env` (environment variables)
  - `AgentCoffeeWeb.py`

## File Modification Times
All tracked files were last modified on **2025-07-07 at 14:09**.

## Environment Requirements
The system requires the following environment variables (stored in `.env` file):
- `OPENAI_API_KEY`: Required for GPT-4 access
- `GOOGLE_MAPS_API_KEY`: Optional for location services
- `OPENWEATHER_API_KEY`: Optional for weather integration
- `REDIS_URL`: Optional for persistent memory storage

## Cache and Build Artifacts
- No Python cache directories (`__pycache__`) present
- No pytest cache directories present
- No build artifacts or egg-info directories present

## Quick Start Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest test_modern_agent.py -v

# Run Streamlit demo
streamlit run modern_agent_demo.py

# Run coffee agent
python agent_coffee.py

# Run MLX variant
python agent_coffee-mlx.py
```

## Architecture Components
1. **State Machine**: IDLE, PLANNING, EXECUTING, ERROR, RECOVERING, COMPLETED
2. **Memory System**: Multi-type memory with optional Redis persistence
3. **Planner**: Goal decomposition with dependency management
4. **Task Queue**: Priority-based concurrent execution
5. **Plugin System**: Extensible actions with validation
6. **Monitoring**: Self-monitoring with metrics and health checks

## Demo Applications
- Coffee shop finder with taste preferences
- Weather integration for optimal experiences
- Route planning to recommended locations
- Interactive Streamlit UI with real-time metrics

## Notes
- Project is marked as "Production Ready" status
- Uses MIT License
- Supports Python 3.8+
- Has comprehensive test coverage
- Includes both synchronous and asynchronous implementations