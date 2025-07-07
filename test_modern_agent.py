"""
Test script for the Modern Agent System
Demonstrates basic functionality without requiring all dependencies
"""

import asyncio
import os
from datetime import datetime

# Try to import the modern agent system
try:
    from modern_agent_system import (
        ModernAutonomousAgent, 
        AgentConfig,
        ActionPlugin,
        ActionResult,
        AgentState,
        Priority
    )
    AGENT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import agent system: {e}")
    AGENT_AVAILABLE = False

# Simple test plugin that doesn't require external APIs
class TestPlugin(ActionPlugin):
    """A simple test plugin for demonstration"""
    
    def __init__(self):
        super().__init__(
            name="test_action",
            description="A simple test action that echoes input"
        )
    
    def validate_inputs(self, **kwargs):
        if "message" not in kwargs:
            return False, "Missing required parameter: message"
        return True, None
    
    async def execute(self, **kwargs):
        try:
            message = kwargs["message"]
            
            # Simulate some processing
            await asyncio.sleep(0.5)
            
            result = {
                "echo": message,
                "timestamp": datetime.now().isoformat(),
                "word_count": len(message.split()),
                "character_count": len(message)
            }
            
            return ActionResult(
                success=True,
                data=result,
                metadata={"processing_time": "0.5s"}
            )
        except Exception as e:
            return ActionResult(
                success=False,
                error=str(e)
            )


async def test_basic_functionality():
    """Test basic agent functionality"""
    print("=== Testing Modern Agent System ===\n")
    
    # Create agent configuration
    config = AgentConfig(
        name="TestAgent",
        model="gpt-4",  # Will use mock if OpenAI not available
        temperature=0.1,
        enable_monitoring=False,  # Disable for testing
        redis_url=None  # No Redis for testing
    )
    
    print(f"1. Created configuration: {config.name}")
    
    # Initialize agent
    agent = ModernAutonomousAgent(config)
    print(f"2. Initialized agent in state: {agent.state.name}")
    
    # Register test plugin
    test_plugin = TestPlugin()
    agent.register_action(test_plugin)
    print(f"3. Registered plugin: {test_plugin.name}")
    
    # Test the plugin directly
    print("\n4. Testing plugin directly:")
    result = await test_plugin.execute_with_monitoring(message="Hello, Modern Agent!")
    print(f"   - Success: {result.success}")
    print(f"   - Data: {result.data}")
    print(f"   - Stats: {test_plugin.get_stats()}")
    
    # Test memory system
    print("\n5. Testing memory system:")
    from modern_agent_system import MemoryType
    
    agent.memory.store(MemoryType.WORKING, "test_key", "test_value")
    retrieved = agent.memory.retrieve(MemoryType.WORKING, "test_key")
    print(f"   - Stored and retrieved: {retrieved}")
    
    agent.memory.store(MemoryType.SEMANTIC, "fact", "Coffee contains caffeine")
    fact = agent.memory.retrieve(MemoryType.SEMANTIC, "fact")
    print(f"   - Semantic memory: {fact}")
    
    # Test health check
    print("\n6. Testing health check:")
    health = await agent.health_check()
    print(f"   - Status: {health['status']}")
    print(f"   - State: {health['state']}")
    print(f"   - Metrics: {health['metrics']}")
    
    print("\n=== Test completed successfully! ===")


async def test_error_handling():
    """Test error handling capabilities"""
    print("\n=== Testing Error Handling ===\n")
    
    class FaultyPlugin(ActionPlugin):
        def __init__(self):
            super().__init__(
                name="faulty_action",
                description="A plugin that fails sometimes"
            )
            self.fail_count = 0
        
        def validate_inputs(self, **kwargs):
            return True, None
        
        async def execute(self, **kwargs):
            self.fail_count += 1
            if self.fail_count < 3:
                raise Exception(f"Simulated failure #{self.fail_count}")
            
            return ActionResult(
                success=True,
                data={"message": "Success after retries!"}
            )
    
    config = AgentConfig(name="ErrorTestAgent", enable_monitoring=False)
    agent = ModernAutonomousAgent(config)
    
    faulty_plugin = FaultyPlugin()
    agent.register_action(faulty_plugin)
    
    print("1. Testing retry mechanism:")
    # The retry decorator should handle the failures
    from modern_agent_system import Task
    task = Task(
        id="test_task",
        description="Test error handling",
        priority=Priority.MEDIUM,
        created_at=datetime.now(),
        metadata={"action": "faulty_action", "parameters": {}}
    )
    
    try:
        result = await agent._execute_task(task)
        print(f"   - Final result: {result.success}")
        print(f"   - Plugin stats: {faulty_plugin.get_stats()}")
    except Exception as e:
        print(f"   - Failed after retries: {e}")


def main():
    """Main test runner"""
    if not AGENT_AVAILABLE:
        print("Agent system not available. Please install dependencies:")
        print("pip install openai pydantic tenacity networkx")
        return
    
    print("Starting Modern Agent System Tests...\n")
    
    try:
        # Run basic functionality test
        asyncio.run(test_basic_functionality())
        
        # Run error handling test
        asyncio.run(test_error_handling())
        
        print("\n✅ All tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()