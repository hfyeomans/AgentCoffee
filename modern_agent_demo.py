"""
Modern Agent System Demo
Interactive Streamlit application to demonstrate the enhanced autonomous agent
"""

import streamlit as st
import asyncio
import json
import os
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Handle imports with fallbacks
try:
    from modern_agent_system import (
        ModernAutonomousAgent, 
        AgentConfig, 
        AgentState,
        Priority
    )
    from example_plugins import (
        CoffeeLocationPlugin,
        CoffeeTastePlugin,
        WeatherPlugin,
        RoutePlugin
    )
    AGENT_AVAILABLE = True
except ImportError as e:
    AGENT_AVAILABLE = False
    st.error(f"Failed to import agent system: {e}")

# Page configuration
st.set_page_config(
    page_title="Modern Coffee Agent",
    page_icon="☕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .stProgress .st-bo {
        background-color: #8B4513;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .agent-state {
        font-size: 1.2rem;
        font-weight: bold;
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        display: inline-block;
    }
    .state-idle { background-color: #e0e0e0; color: #333; }
    .state-planning { background-color: #bbdefb; color: #1565c0; }
    .state-executing { background-color: #c8e6c9; color: #2e7d32; }
    .state-error { background-color: #ffcdd2; color: #c62828; }
    .state-completed { background-color: #b2dfdb; color: #00695c; }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        border-left: 4px solid #1976d2;
    }
    .agent-message {
        background-color: #f3e5f5;
        border-left: 4px solid #7b1fa2;
    }
    .system-message {
        background-color: #fff3e0;
        border-left: 4px solid #f57c00;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None
    st.session_state.agent_state = AgentState.IDLE if AGENT_AVAILABLE else None
    st.session_state.conversation_history = []
    st.session_state.metrics_history = []
    st.session_state.task_queue = []

# Helper functions
async def initialize_agent():
    """Initialize the modern agent with plugins"""
    config = AgentConfig(
        name="ModernCoffeeAgent",
        model="gpt-4",
        temperature=0.1,
        enable_monitoring=True,
        max_concurrent_tasks=3
    )
    
    agent = ModernAutonomousAgent(config)
    
    # Register plugins
    agent.register_action(CoffeeLocationPlugin())
    agent.register_action(CoffeeTastePlugin())
    agent.register_action(WeatherPlugin())
    agent.register_action(RoutePlugin())
    
    # Start monitoring
    monitoring_task = asyncio.create_task(agent.start_monitoring())
    
    return agent, monitoring_task

def display_agent_state(state: AgentState):
    """Display agent state with styling"""
    state_class = f"state-{state.name.lower()}"
    st.markdown(
        f'<div class="agent-state {state_class}">Agent State: {state.name}</div>',
        unsafe_allow_html=True
    )

def display_metrics(agent):
    """Display agent metrics"""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Tasks Completed", agent.metrics["tasks_completed"])
    
    with col2:
        st.metric("Tasks Failed", agent.metrics["tasks_failed"])
    
    with col3:
        success_rate = (
            agent.metrics["tasks_completed"] / 
            (agent.metrics["tasks_completed"] + agent.metrics["tasks_failed"])
            if (agent.metrics["tasks_completed"] + agent.metrics["tasks_failed"]) > 0
            else 0
        )
        st.metric("Success Rate", f"{success_rate:.1%}")
    
    with col4:
        uptime = (datetime.now() - agent.metrics["uptime_start"]).total_seconds()
        st.metric("Uptime", f"{uptime/60:.1f} min")

def display_memory_usage(agent):
    """Display memory usage visualization"""
    memory_data = {
        "Memory Type": ["Working", "Episodic", "Semantic"],
        "Count": [
            len(agent.memory.working_memory),
            len(agent.memory.episodic_memory),
            len(agent.memory.semantic_memory)
        ]
    }
    
    fig = px.bar(
        memory_data, 
        x="Memory Type", 
        y="Count",
        title="Memory Usage",
        color="Memory Type",
        color_discrete_map={
            "Working": "#1976d2",
            "Episodic": "#388e3c",
            "Semantic": "#7b1fa2"
        }
    )
    fig.update_layout(height=300, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

def display_action_stats(agent):
    """Display action plugin statistics"""
    stats_data = []
    for name, action in agent.action_plugins.items():
        stats = action.get_stats()
        stats_data.append({
            "Action": name,
            "Executions": stats["executions"],
            "Success Rate": stats["success_rate"],
            "Avg Time (s)": stats["avg_execution_time"]
        })
    
    if stats_data:
        df = pd.DataFrame(stats_data)
        st.dataframe(df, use_container_width=True)

# Main application
def main():
    st.title("☕ Modern Autonomous Coffee Agent")
    st.markdown("An advanced AI agent with state management, planning, and memory systems")
    
    # Sidebar
    with st.sidebar:
        st.header("🎛️ Agent Control")
        
        if AGENT_AVAILABLE:
            # Initialize agent button
            if st.button("Initialize Agent", disabled=(st.session_state.agent is not None)):
                with st.spinner("Initializing agent..."):
                    agent, monitoring = asyncio.run(initialize_agent())
                    st.session_state.agent = agent
                    st.session_state.monitoring_task = monitoring
                    st.success("Agent initialized successfully!")
                    st.rerun()
            
            # Agent status
            if st.session_state.agent:
                st.divider()
                display_agent_state(st.session_state.agent.state)
                
                # Health check
                if st.button("🏥 Health Check"):
                    health = asyncio.run(st.session_state.agent.health_check())
                    st.json(health)
                
                # Memory management
                st.divider()
                st.subheader("💾 Memory Management")
                
                if st.button("Clear Working Memory"):
                    st.session_state.agent.memory.working_memory.clear()
                    st.success("Working memory cleared")
                
                # Agent configuration
                st.divider()
                st.subheader("⚙️ Configuration")
                
                temp = st.slider(
                    "Temperature",
                    min_value=0.0,
                    max_value=2.0,
                    value=st.session_state.agent.config.temperature,
                    step=0.1
                )
                if temp != st.session_state.agent.config.temperature:
                    st.session_state.agent.config.temperature = temp
                
                max_tasks = st.number_input(
                    "Max Concurrent Tasks",
                    min_value=1,
                    max_value=10,
                    value=st.session_state.agent.config.max_concurrent_tasks
                )
                if max_tasks != st.session_state.agent.config.max_concurrent_tasks:
                    st.session_state.agent.config.max_concurrent_tasks = max_tasks
        
        # Examples
        st.divider()
        st.subheader("📝 Example Queries")
        examples = [
            "Find coffee shops in Boston that serve strong coffee",
            "I like creamy and smooth coffee, what should I try?",
            "What's the weather like in Seattle for a coffee walk?",
            "Find the best route from MIT to a nearby coffee shop",
            "Recommend a coffee for someone who likes chocolatey and less acidic flavors"
        ]
        
        for example in examples:
            if st.button(example, key=f"ex_{example[:20]}"):
                st.session_state.user_input = example
    
    # Main content area
    if not AGENT_AVAILABLE:
        st.error("Agent system not available. Please install required dependencies.")
        st.code("pip install -r requirements.txt", language="bash")
        return
    
    if st.session_state.agent is None:
        st.info("👈 Click 'Initialize Agent' in the sidebar to get started")
        return
    
    # Metrics dashboard
    with st.expander("📊 Agent Metrics", expanded=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            display_metrics(st.session_state.agent)
        
        with col2:
            display_memory_usage(st.session_state.agent)
        
        st.divider()
        st.subheader("Action Plugin Statistics")
        display_action_stats(st.session_state.agent)
    
    # Chat interface
    st.divider()
    st.subheader("💬 Chat with Agent")
    
    # Display conversation history
    for message in st.session_state.conversation_history:
        if message["role"] == "user":
            st.markdown(
                f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>',
                unsafe_allow_html=True
            )
        elif message["role"] == "agent":
            st.markdown(
                f'<div class="chat-message agent-message"><strong>Agent:</strong> {message["content"]}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="chat-message system-message"><strong>System:</strong> {message["content"]}</div>',
                unsafe_allow_html=True
            )
    
    # Input area
    col1, col2 = st.columns([5, 1])
    
    with col1:
        user_input = st.text_input(
            "Ask the agent something...",
            value=st.session_state.get("user_input", ""),
            key="query_input"
        )
    
    with col2:
        send_button = st.button("Send", type="primary", use_container_width=True)
    
    if send_button and user_input:
        # Add user message
        st.session_state.conversation_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now()
        })
        
        # Process with agent
        with st.spinner("Agent is thinking..."):
            try:
                # Update UI to show planning state
                st.session_state.agent_state = AgentState.PLANNING
                
                # Get response
                response = asyncio.run(
                    st.session_state.agent.process_request(user_input)
                )
                
                # Add agent response
                st.session_state.conversation_history.append({
                    "role": "agent",
                    "content": response,
                    "timestamp": datetime.now()
                })
                
                # Clear input
                st.session_state.user_input = ""
                
            except Exception as e:
                st.session_state.conversation_history.append({
                    "role": "system",
                    "content": f"Error: {str(e)}",
                    "timestamp": datetime.now()
                })
        
        st.rerun()
    
    # Task queue visualization
    with st.expander("🔄 Task Queue", expanded=False):
        if hasattr(st.session_state.agent, 'planner') and st.session_state.agent.planner.plan_graph:
            # Create a simple visualization of the task graph
            nodes = list(st.session_state.agent.planner.plan_graph.nodes())
            edges = list(st.session_state.agent.planner.plan_graph.edges())
            
            if nodes:
                st.write(f"Current plan has {len(nodes)} tasks")
                
                # Task status
                task_data = []
                for node in nodes:
                    task = st.session_state.agent.planner.plan_graph.nodes[node]["task"]
                    task_data.append({
                        "ID": task.id[:8],
                        "Description": task.description[:50] + "...",
                        "Priority": task.priority.name,
                        "Status": task.status,
                        "Dependencies": len(task.dependencies)
                    })
                
                df = pd.DataFrame(task_data)
                st.dataframe(df, use_container_width=True)
    
    # Clear chat button
    if st.button("🗑️ Clear Conversation"):
        st.session_state.conversation_history = []
        st.rerun()

if __name__ == "__main__":
    main()