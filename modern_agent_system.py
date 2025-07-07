"""
Modern Autonomous Agent System
A production-ready, deterministic agent with advanced features including:
- State machine for deterministic behavior
- Plugin-based action system
- Memory management (short-term and long-term)
- Advanced planning and goal decomposition
- Robust error handling and recovery
- Async operations and concurrency
- Self-monitoring and health checks
"""

import asyncio
import json
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
from collections import deque
import hashlib
import pickle

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Handle optional imports gracefully
try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    logger.warning("aiohttp not available - some features may be limited")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logger.warning("numpy not available - similarity calculations will be simplified")

from pydantic import BaseModel, Field, validator

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI not available - agent will use mock responses")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None
    logger.warning("Redis not available - persistent memory disabled")

from tenacity import retry, stop_after_attempt, wait_exponential
import networkx as nx


# ============= Core Data Models =============

class AgentState(Enum):
    """Agent states for deterministic behavior"""
    IDLE = auto()
    PLANNING = auto()
    EXECUTING = auto()
    WAITING = auto()
    ERROR = auto()
    RECOVERING = auto()
    COMPLETED = auto()


class Priority(Enum):
    """Task priority levels"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5


@dataclass
class Task:
    """Represents a task to be executed by the agent"""
    id: str
    description: str
    priority: Priority
    created_at: datetime
    deadline: Optional[datetime] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    retries: int = 0
    max_retries: int = 3
    status: str = "pending"
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class ActionResult:
    """Result of an action execution"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class AgentConfig(BaseModel):
    """Configuration for the agent"""
    name: str = "ModernAgent"
    model: str = "gpt-4"
    temperature: float = 0.1
    max_tokens: int = 2000
    max_concurrent_tasks: int = 5
    memory_size: int = 1000
    enable_learning: bool = True
    enable_monitoring: bool = True
    redis_url: Optional[str] = None
    
    @validator('temperature')
    def temperature_range(cls, v):
        if not 0 <= v <= 2:
            raise ValueError('Temperature must be between 0 and 2')
        return v


# ============= Memory Systems =============

class MemoryType(Enum):
    """Types of memory storage"""
    WORKING = "working"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class Memory:
    """Advanced memory system with multiple storage types"""
    
    def __init__(self, redis_url: Optional[str] = None, max_size: int = 1000):
        self.max_size = max_size
        self.working_memory: deque = deque(maxlen=100)
        self.episodic_memory: List[Dict] = []
        self.semantic_memory: Dict[str, Any] = {}
        self.procedural_memory: Dict[str, Callable] = {}
        
        # Redis for persistent memory
        self.redis_client = None
        if redis_url:
            try:
                self.redis_client = redis.from_url(redis_url)
                logger.info("Connected to Redis for persistent memory")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}")
    
    def store(self, memory_type: MemoryType, key: str, value: Any) -> None:
        """Store information in memory"""
        if memory_type == MemoryType.WORKING:
            self.working_memory.append({
                "key": key,
                "value": value,
                "timestamp": datetime.now()
            })
        elif memory_type == MemoryType.EPISODIC:
            self.episodic_memory.append({
                "key": key,
                "value": value,
                "timestamp": datetime.now()
            })
            # Persist to Redis if available
            if self.redis_client:
                self._persist_to_redis(f"episodic:{key}", value)
        elif memory_type == MemoryType.SEMANTIC:
            self.semantic_memory[key] = value
            if self.redis_client:
                self._persist_to_redis(f"semantic:{key}", value)
        elif memory_type == MemoryType.PROCEDURAL:
            if callable(value):
                self.procedural_memory[key] = value
    
    def retrieve(self, memory_type: MemoryType, key: str) -> Optional[Any]:
        """Retrieve information from memory"""
        if memory_type == MemoryType.WORKING:
            for item in reversed(self.working_memory):
                if item["key"] == key:
                    return item["value"]
        elif memory_type == MemoryType.EPISODIC:
            # Check Redis first
            if self.redis_client:
                value = self._retrieve_from_redis(f"episodic:{key}")
                if value:
                    return value
            # Fall back to local memory
            for item in self.episodic_memory:
                if item["key"] == key:
                    return item["value"]
        elif memory_type == MemoryType.SEMANTIC:
            if self.redis_client:
                value = self._retrieve_from_redis(f"semantic:{key}")
                if value:
                    return value
            return self.semantic_memory.get(key)
        elif memory_type == MemoryType.PROCEDURAL:
            return self.procedural_memory.get(key)
        return None
    
    def _persist_to_redis(self, key: str, value: Any) -> None:
        """Persist value to Redis"""
        try:
            self.redis_client.set(key, pickle.dumps(value), ex=86400)  # 24 hour expiry
        except Exception as e:
            logger.error(f"Failed to persist to Redis: {e}")
    
    def _retrieve_from_redis(self, key: str) -> Optional[Any]:
        """Retrieve value from Redis"""
        try:
            value = self.redis_client.get(key)
            return pickle.loads(value) if value else None
        except Exception as e:
            logger.error(f"Failed to retrieve from Redis: {e}")
            return None
    
    def search_similar(self, query: str, memory_type: MemoryType, top_k: int = 5) -> List[Tuple[str, Any, float]]:
        """Search for similar memories using semantic similarity"""
        # This is a simplified version - in production, you'd use embeddings
        results = []
        
        if memory_type == MemoryType.EPISODIC:
            memories = self.episodic_memory
        elif memory_type == MemoryType.SEMANTIC:
            memories = [{"key": k, "value": v} for k, v in self.semantic_memory.items()]
        else:
            return results
        
        for memory in memories:
            # Simple similarity based on string matching
            similarity = self._calculate_similarity(query, str(memory["value"]))
            results.append((memory["key"], memory["value"], similarity))
        
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:top_k]
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate simple text similarity"""
        # In production, use proper embeddings
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union) if union else 0.0


# ============= Action Plugin System =============

class ActionPlugin(ABC):
    """Base class for action plugins"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.execution_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.average_execution_time = 0.0
    
    @abstractmethod
    async def execute(self, **kwargs) -> ActionResult:
        """Execute the action"""
        pass
    
    @abstractmethod
    def validate_inputs(self, **kwargs) -> Tuple[bool, Optional[str]]:
        """Validate input parameters"""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        return {
            "name": self.name,
            "executions": self.execution_count,
            "successes": self.success_count,
            "failures": self.failure_count,
            "success_rate": self.success_count / self.execution_count if self.execution_count > 0 else 0,
            "avg_execution_time": self.average_execution_time
        }
    
    async def execute_with_monitoring(self, **kwargs) -> ActionResult:
        """Execute action with monitoring"""
        start_time = time.time()
        
        try:
            # Validate inputs
            valid, error = self.validate_inputs(**kwargs)
            if not valid:
                self.failure_count += 1
                return ActionResult(success=False, error=error)
            
            # Execute action
            result = await self.execute(**kwargs)
            
            # Update stats
            self.execution_count += 1
            if result.success:
                self.success_count += 1
            else:
                self.failure_count += 1
            
            # Update average execution time
            execution_time = time.time() - start_time
            self.average_execution_time = (
                (self.average_execution_time * (self.execution_count - 1) + execution_time) 
                / self.execution_count
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing action {self.name}: {e}")
            self.failure_count += 1
            self.execution_count += 1
            return ActionResult(success=False, error=str(e))


# ============= Planning System =============

class Planner:
    """Advanced planning system with goal decomposition"""
    
    def __init__(self, llm_client: AsyncOpenAI):
        self.llm_client = llm_client
        self.plan_graph = nx.DiGraph()
        self.current_plan = None
    
    async def create_plan(self, goal: str, available_actions: List[str], context: Dict[str, Any]) -> List[Task]:
        """Create a plan to achieve the goal"""
        prompt = f"""
        Create a detailed step-by-step plan to achieve the following goal:
        Goal: {goal}
        
        Available actions: {', '.join(available_actions)}
        Context: {json.dumps(context, indent=2)}
        
        Return a JSON array of steps, each with:
        - description: what to do
        - action: which action to use
        - parameters: parameters for the action
        - dependencies: array of step indices this depends on
        - priority: "critical", "high", "medium", or "low"
        """
        
        response = await self.llm_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a planning assistant. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        try:
            plan_data = json.loads(response.choices[0].message.content)
            tasks = []
            
            for i, step in enumerate(plan_data.get("steps", [])):
                task = Task(
                    id=f"task_{hashlib.md5(f'{goal}_{i}'.encode()).hexdigest()[:8]}",
                    description=step["description"],
                    priority=Priority[step["priority"].upper()],
                    created_at=datetime.now(),
                    dependencies=step.get("dependencies", []),
                    metadata={
                        "action": step["action"],
                        "parameters": step.get("parameters", {})
                    }
                )
                tasks.append(task)
                
                # Add to plan graph
                self.plan_graph.add_node(task.id, task=task)
                for dep in task.dependencies:
                    if f"task_{dep}" in self.plan_graph:
                        self.plan_graph.add_edge(f"task_{dep}", task.id)
            
            return tasks
            
        except Exception as e:
            logger.error(f"Failed to create plan: {e}")
            # Return a simple single-task plan as fallback
            return [Task(
                id=f"task_{hashlib.md5(goal.encode()).hexdigest()[:8]}",
                description=goal,
                priority=Priority.MEDIUM,
                created_at=datetime.now()
            )]
    
    def get_next_executable_tasks(self) -> List[Task]:
        """Get tasks that can be executed now"""
        executable = []
        
        for node in self.plan_graph.nodes():
            task = self.plan_graph.nodes[node]["task"]
            
            # Check if all dependencies are completed
            dependencies_met = all(
                self.plan_graph.nodes.get(dep, {}).get("task", {}).status == "completed"
                for dep in task.dependencies
            )
            
            if task.status == "pending" and dependencies_met:
                executable.append(task)
        
        return sorted(executable, key=lambda t: t.priority.value)
    
    def update_task_status(self, task_id: str, status: str, result: Any = None) -> None:
        """Update task status in the plan"""
        if task_id in self.plan_graph:
            task = self.plan_graph.nodes[task_id]["task"]
            task.status = status
            task.result = result


# ============= Main Agent Class =============

class ModernAutonomousAgent:
    """Modern autonomous agent with advanced features"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.state = AgentState.IDLE
        self.memory = Memory(redis_url=config.redis_url, max_size=config.memory_size)
        self.llm_client = AsyncOpenAI()
        self.planner = Planner(self.llm_client)
        self.action_plugins: Dict[str, ActionPlugin] = {}
        self.task_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.monitoring_enabled = config.enable_monitoring
        self.health_status = {"healthy": True, "last_check": datetime.now()}
        
        # Initialize metrics
        self.metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "average_task_time": 0.0,
            "uptime_start": datetime.now()
        }
        
        logger.info(f"Initialized {config.name} agent")
    
    def register_action(self, action: ActionPlugin) -> None:
        """Register an action plugin"""
        self.action_plugins[action.name] = action
        logger.info(f"Registered action: {action.name}")
    
    async def process_request(self, request: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Process a user request"""
        try:
            self.state = AgentState.PLANNING
            
            # Store request in working memory
            self.memory.store(MemoryType.WORKING, "current_request", request)
            
            # Search for relevant past experiences
            similar_experiences = self.memory.search_similar(
                request, MemoryType.EPISODIC, top_k=3
            )
            
            # Create execution plan
            tasks = await self.planner.create_plan(
                goal=request,
                available_actions=list(self.action_plugins.keys()),
                context={
                    "user_context": context or {},
                    "similar_experiences": similar_experiences
                }
            )
            
            # Execute plan
            self.state = AgentState.EXECUTING
            results = await self._execute_plan(tasks)
            
            # Store experience
            self.memory.store(MemoryType.EPISODIC, request, {
                "request": request,
                "plan": [t.description for t in tasks],
                "results": results,
                "timestamp": datetime.now()
            })
            
            # Generate response
            response = await self._generate_response(request, results)
            
            self.state = AgentState.COMPLETED
            return response
            
        except Exception as e:
            logger.error(f"Error processing request: {e}")
            self.state = AgentState.ERROR
            await self._handle_error(e)
            return f"I encountered an error while processing your request: {str(e)}"
    
    async def _execute_plan(self, tasks: List[Task]) -> List[ActionResult]:
        """Execute a plan with concurrent task execution"""
        results = []
        
        # Add tasks to queue
        for task in tasks:
            await self.task_queue.put((task.priority.value, task))
        
        # Execute tasks concurrently
        workers = []
        for i in range(min(self.config.max_concurrent_tasks, len(tasks))):
            worker = asyncio.create_task(self._task_worker())
            workers.append(worker)
        
        # Wait for all tasks to complete
        await self.task_queue.join()
        
        # Cancel workers
        for worker in workers:
            worker.cancel()
        
        # Collect results
        for task in tasks:
            if task.result:
                results.append(task.result)
        
        return results
    
    async def _task_worker(self) -> None:
        """Worker to process tasks from the queue"""
        while True:
            try:
                priority, task = await self.task_queue.get()
                
                # Check dependencies
                while not all(t.status == "completed" for t_id in task.dependencies 
                             for t in [self.planner.plan_graph.nodes.get(t_id, {}).get("task")]):
                    await asyncio.sleep(0.1)
                
                # Execute task
                result = await self._execute_task(task)
                task.result = result
                task.status = "completed" if result.success else "failed"
                
                # Update metrics
                if result.success:
                    self.metrics["tasks_completed"] += 1
                else:
                    self.metrics["tasks_failed"] += 1
                
                self.task_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Task worker error: {e}")
                self.task_queue.task_done()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _execute_task(self, task: Task) -> ActionResult:
        """Execute a single task with retry logic"""
        action_name = task.metadata.get("action", "unknown")
        parameters = task.metadata.get("parameters", {})
        
        if action_name not in self.action_plugins:
            return ActionResult(success=False, error=f"Unknown action: {action_name}")
        
        action = self.action_plugins[action_name]
        result = await action.execute_with_monitoring(**parameters)
        
        return result
    
    async def _generate_response(self, request: str, results: List[ActionResult]) -> str:
        """Generate a natural language response"""
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        prompt = f"""
        Generate a helpful response to the user's request based on the execution results.
        
        User request: {request}
        
        Successful actions:
        {json.dumps([{"data": r.data, "metadata": r.metadata} for r in successful_results], indent=2)}
        
        Failed actions:
        {json.dumps([{"error": r.error} for r in failed_results], indent=2)}
        
        Provide a natural, helpful response that summarizes the results.
        """
        
        response = await self.llm_client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.config.temperature
        )
        
        return response.choices[0].message.content
    
    async def _handle_error(self, error: Exception) -> None:
        """Handle errors with recovery strategies"""
        self.state = AgentState.RECOVERING
        
        # Log error
        logger.error(f"Agent error: {error}")
        
        # Store error in memory for learning
        self.memory.store(MemoryType.EPISODIC, f"error_{datetime.now()}", {
            "error": str(error),
            "state": self.state.name,
            "timestamp": datetime.now()
        })
        
        # Attempt recovery based on error type
        if isinstance(error, asyncio.TimeoutError):
            # Reset task queue
            while not self.task_queue.empty():
                self.task_queue.get_nowait()
        elif isinstance(error, ConnectionError):
            # Wait and retry
            await asyncio.sleep(5)
        
        self.state = AgentState.IDLE
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        health_data = {
            "status": "healthy",
            "state": self.state.name,
            "metrics": self.metrics,
            "memory_usage": {
                "working": len(self.memory.working_memory),
                "episodic": len(self.memory.episodic_memory),
                "semantic": len(self.memory.semantic_memory)
            },
            "action_stats": {
                name: action.get_stats() 
                for name, action in self.action_plugins.items()
            },
            "uptime": (datetime.now() - self.metrics["uptime_start"]).total_seconds()
        }
        
        # Check for issues
        if self.state == AgentState.ERROR:
            health_data["status"] = "error"
        elif self.metrics["tasks_failed"] > self.metrics["tasks_completed"] * 0.5:
            health_data["status"] = "degraded"
        
        self.health_status = {
            "healthy": health_data["status"] == "healthy",
            "last_check": datetime.now(),
            "data": health_data
        }
        
        return health_data
    
    async def start_monitoring(self) -> None:
        """Start autonomous monitoring"""
        if not self.monitoring_enabled:
            return
        
        while self.monitoring_enabled:
            try:
                # Perform health check
                health_data = await self.health_check()
                
                # Take action if unhealthy
                if health_data["status"] != "healthy":
                    logger.warning(f"Health check failed: {health_data}")
                    await self._handle_error(Exception("Health check failed"))
                
                # Clean up old memories
                if len(self.memory.episodic_memory) > self.config.memory_size:
                    self.memory.episodic_memory = self.memory.episodic_memory[-self.config.memory_size:]
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(60)


# ============= Example Implementation =============

if __name__ == "__main__":
    # This would be in a separate file in production
    from example_plugins import CoffeeLocationPlugin, CoffeeTastePlugin, WeatherPlugin
    
    async def main():
        # Initialize agent
        config = AgentConfig(
            name="CoffeeExpertAgent",
            model="gpt-4",
            temperature=0.1,
            enable_monitoring=True
        )
        
        agent = ModernAutonomousAgent(config)
        
        # Register plugins
        agent.register_action(CoffeeLocationPlugin())
        agent.register_action(CoffeeTastePlugin())
        agent.register_action(WeatherPlugin())
        
        # Start monitoring in background
        monitoring_task = asyncio.create_task(agent.start_monitoring())
        
        # Process requests
        response = await agent.process_request(
            "Find me a coffee shop in Boston that serves strong coffee, and check if it's good weather to walk there"
        )
        
        print(response)
        
        # Check health
        health = await agent.health_check()
        print(f"Agent health: {json.dumps(health, indent=2)}")
        
        # Cleanup
        agent.monitoring_enabled = False
        await monitoring_task
    
    # Run the agent
    asyncio.run(main())