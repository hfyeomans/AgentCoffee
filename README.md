# 🤖 Modern Autonomous Agent System

A production-ready, deterministic AI agent system with advanced features including state management, plugin architecture, multi-type memory systems, intelligent planning, and self-monitoring capabilities.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green)
![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 🚀 Features

### Core Capabilities
- **🎯 Deterministic State Machine**: Predictable behavior with explicit state transitions (IDLE, PLANNING, EXECUTING, ERROR, RECOVERING, COMPLETED)
- **🧩 Plugin Architecture**: Extensible action system with validation, monitoring, and performance metrics
- **🧠 Advanced Memory Systems**: 
  - Working Memory (short-term task context)
  - Episodic Memory (past experiences)
  - Semantic Memory (facts and knowledge)
  - Procedural Memory (learned procedures)
  - Optional Redis persistence
- **📋 Intelligent Planning**: Multi-step goal decomposition with dependency graphs and priority-based execution
- **⚡ Concurrent Execution**: Parallel task processing with configurable concurrency limits
- **🛡️ Robust Error Handling**: Retry mechanisms, graceful degradation, and self-recovery
- **📊 Self-Monitoring**: Health checks, performance metrics, and automatic optimization

### Demo Applications
- **☕ Coffee Agent**: Find coffee shops, get recommendations based on taste preferences
- **🌤️ Weather Integration**: Check weather conditions for optimal coffee experiences
- **🗺️ Route Planning**: Calculate routes to recommended locations
- **💬 Interactive UI**: Beautiful Streamlit interface with real-time metrics

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- OpenAI API key (for GPT-4 access)
- Optional: Redis for persistent memory
- Optional: API keys for weather and maps services

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/modern-agent-system.git
cd modern-agent-system
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
# Create .env file
cat > .env << EOF
OPENAI_API_KEY=your_openai_key_here
GOOGLE_MAPS_API_KEY=your_google_maps_key_here  # Optional
OPENWEATHER_API_KEY=your_openweather_key_here  # Optional
REDIS_URL=redis://localhost:6379  # Optional
EOF
```

4. **Run the demo**
```bash
streamlit run modern_agent_demo.py
```

### Docker Setup (Optional)

For Redis persistence:
```bash
docker run -d -p 6379:6379 redis:alpine
```

## 🎮 Usage

### Basic Example

```python
import asyncio
from modern_agent_system import ModernAutonomousAgent, AgentConfig
from example_plugins import CoffeeLocationPlugin, WeatherPlugin

async def main():
    # Configure agent
    config = AgentConfig(
        name="MyAgent",
        model="gpt-4",
        temperature=0.1,
        max_concurrent_tasks=5,
        enable_monitoring=True
    )
    
    # Initialize agent
    agent = ModernAutonomousAgent(config)
    
    # Register plugins
    agent.register_action(CoffeeLocationPlugin())
    agent.register_action(WeatherPlugin())
    
    # Process request
    response = await agent.process_request(
        "Find a coffee shop in Boston with outdoor seating and good weather"
    )
    print(response)

asyncio.run(main())
```

### Creating Custom Plugins

```python
from modern_agent_system import ActionPlugin, ActionResult

class CustomPlugin(ActionPlugin):
    def __init__(self):
        super().__init__(
            name="custom_action",
            description="Your custom action description"
        )
    
    def validate_inputs(self, **kwargs):
        # Validate required parameters
        if "required_param" not in kwargs:
            return False, "Missing required parameter"
        return True, None
    
    async def execute(self, **kwargs):
        try:
            # Your action logic here
            result = await your_async_operation(kwargs["required_param"])
            
            return ActionResult(
                success=True,
                data=result,
                metadata={"execution_time": "fast"}
            )
        except Exception as e:
            return ActionResult(success=False, error=str(e))
```

### Advanced Configuration

```python
config = AgentConfig(
    name="AdvancedAgent",
    model="gpt-4",
    temperature=0.0,  # More deterministic
    max_tokens=4000,  # Longer responses
    max_concurrent_tasks=10,  # Higher parallelism
    memory_size=5000,  # Larger memory
    enable_learning=True,  # Enable learning from experiences
    enable_monitoring=True,  # Enable self-monitoring
    redis_url="redis://localhost:6379"  # Persistent memory
)
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Modern Agent System                    │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │   Planner   │  │ Task Queue   │  │ Memory System │ │
│  │             │  │              │  │               │ │
│  │ - Goal      │  │ - Priority   │  │ - Working     │ │
│  │   Decomp.   │  │   Queue      │  │ - Episodic    │ │
│  │ - Dep.      │  │ - Concurrent │  │ - Semantic    │ │
│  │   Graph     │  │   Execution  │  │ - Procedural  │ │
│  └─────────────┘  └──────────────┘  └───────────────┘ │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Action Plugin System                │   │
│  │                                                  │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐       │   │
│  │  │ Coffee   │ │ Weather  │ │  Route   │  ...  │   │
│  │  │ Plugins  │ │  Check   │ │  Calc    │       │   │
│  │  └──────────┘ └──────────┘ └──────────┘       │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐ │
│  │   State     │  │  Monitoring  │  │  LLM Client   │ │
│  │  Machine    │  │   & Health   │  │  (GPT-4)      │ │
│  └─────────────┘  └──────────────┘  └───────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Key Components

1. **State Machine**: Manages agent behavior with clear state transitions
2. **Memory System**: Multi-type memory for different kinds of information
3. **Planner**: Decomposes goals into executable tasks with dependencies
4. **Task Queue**: Priority-based concurrent task execution
5. **Plugin System**: Extensible actions with built-in validation
6. **Monitoring**: Self-monitoring with health checks and metrics

## 📊 Streamlit Demo

The included Streamlit demo (`modern_agent_demo.py`) provides:

- **Interactive Chat Interface**: Talk to the agent naturally
- **Real-time Metrics**: Monitor task completion, success rates, and performance
- **Memory Visualization**: See how the agent uses different memory types
- **Task Queue Monitoring**: Watch the agent plan and execute tasks
- **Plugin Statistics**: Track performance of individual actions
- **Configuration Controls**: Adjust agent parameters on the fly

### Running the Demo

```bash
streamlit run modern_agent_demo.py
```

Then open http://localhost:8501 in your browser.

## 🧪 Testing

Run the test suite:

```bash
pytest test_modern_agent.py -v
```

## 📁 Project Structure

```
modern-agent-system/
├── modern_agent_system.py      # Core agent implementation
├── example_plugins.py          # Example action plugins
├── modern_agent_demo.py        # Streamlit demo application
├── test_modern_agent.py        # Test suite
├── requirements.txt            # Dependencies
├── AGENT_UPGRADE_GUIDE.md      # Detailed upgrade documentation
├── README.md                   # This file
└── .env.example               # Environment variables template
```

## 🔧 Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | "ModernAgent" | Agent identifier |
| `model` | str | "gpt-4" | OpenAI model to use |
| `temperature` | float | 0.1 | LLM temperature (0-2) |
| `max_tokens` | int | 2000 | Maximum response tokens |
| `max_concurrent_tasks` | int | 5 | Parallel task limit |
| `memory_size` | int | 1000 | Memory storage limit |
| `enable_learning` | bool | True | Learn from experiences |
| `enable_monitoring` | bool | True | Self-monitoring |
| `redis_url` | str | None | Redis connection URL |

## 🎯 Example Use Cases

### Coffee Finder
```python
response = await agent.process_request(
    "Find a quiet coffee shop in Cambridge with WiFi and good espresso"
)
```

### Multi-step Planning
```python
response = await agent.process_request(
    "Plan a coffee tour of Boston's best shops, considering weather and travel time"
)
```

### Preference Learning
```python
response = await agent.process_request(
    "I like smooth, chocolatey coffee with low acidity. What should I order?"
)
```

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run linting
flake8 .

# Run type checking
mypy .

# Format code
black .
```

## 📈 Performance Metrics

The agent tracks various performance metrics:

- **Task Success Rate**: Percentage of successfully completed tasks
- **Average Execution Time**: Mean time to complete tasks
- **Memory Efficiency**: Usage across different memory types
- **Plugin Performance**: Individual action statistics
- **Concurrent Execution**: Parallel task processing metrics

## 🔒 Security Considerations

- API keys are loaded from environment variables
- Memory can be encrypted when using Redis
- Input validation on all plugin parameters
- Rate limiting on API calls
- Graceful handling of malformed requests

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install -r requirements.txt
   ```

2. **API Key Issues**
   - Verify `.env` file exists and contains valid keys
   - Check API key permissions and quotas

3. **Memory Issues**
   - Reduce `memory_size` in config
   - Enable Redis for memory offloading
   - Clear old memories periodically

4. **Performance Issues**
   - Increase `max_concurrent_tasks`
   - Use a faster model (e.g., gpt-3.5-turbo)
   - Enable caching for repeated operations

## 📚 Additional Resources

- [AGENT_UPGRADE_GUIDE.md](AGENT_UPGRADE_GUIDE.md) - Detailed upgrade documentation
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Streamlit Documentation](https://docs.streamlit.io)
- [Redis Documentation](https://redis.io/docs)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- Streamlit for the demo framework
- The open-source community for various dependencies

---

**Note**: This is an advanced autonomous agent system designed for production use. For simpler use cases, consider starting with basic examples and gradually adding features as needed.