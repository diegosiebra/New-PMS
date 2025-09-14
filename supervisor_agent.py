"""
Supervisor Agent - Multi-Agent Coordinator
Uses langgraph-supervisor to coordinate between Mike and Lara agents
All configurations loaded from database
"""

import os
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langgraph_supervisor import create_supervisor
import logging
from langchain_core.tracers import ConsoleCallbackHandler
from langchain_core.callbacks import CallbackManager

logger = logging.getLogger(__name__)

class SupervisorAgent:
    """Supervisor Agent for coordinating agents"""
    
    def __init__(self, tenant_id: str, agents: List[Any], supervisor_config: Dict[str, Any] = None):
        self.tenant_id = tenant_id
        self.agents = agents
        self.supervisor_config = supervisor_config or {}
        self.model_name = self.supervisor_config.get("model", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
        self.configuration = self.supervisor_config.get("configuration", {})
        self.prompt = self.supervisor_config.get("prompt", self._get_default_prompt())
        self.model = ChatOpenAI(model=self.model_name, temperature=1)
        self.supervisor = None
        self._create_supervisor()
    
    def _create_supervisor(self):
        """Create the supervisor agent using langgraph-supervisor"""
        
        # Extract agent instances from our agent objects
        agent_instances = []
        for agent in self.agents:
            if hasattr(agent, 'get_agent'):
                agent_instances.append(agent.get_agent())
            else:
                agent_instances.append(agent)
        
        # Create the supervisor using langgraph-supervisor - formato do exemplo
        self.supervisor = create_supervisor(
            agents=agent_instances,
            model=self.model,
            prompt=self.prompt,
            output_mode="full_history"
        ).compile()
        
        logger.info(f"Supervisor agent created for tenant {self.tenant_id} with {len(agent_instances)} agents")
    
    def _get_default_prompt(self) -> str:
        """Get default prompt when no configuration is available"""
        return """You are a Supervisor coordinating two specialists:

- mike: handles document validation, check-in processes, and document-related questions.
- lara: handles general support, property information, amenities, and general guest questions.

Your goal is to satisfy the user's intent efficiently by automatically executing the appropriate agent.

Routing:
- If the request is about documents, check-in, or validation, use mike.
- If the request is about property info, amenities, general support, or recommendations, use lara.
- If the request is a simple greeting or basic question, respond directly.

Be decisive: when you have enough information, proceed with the appropriate agent without asking for confirmation. The agent will be executed automatically."""
    
    def get_supervisor(self):
        """Get the created supervisor"""
        return self.supervisor
    
    def invoke(self, input_data):
        """Invoke the supervisor and return the result"""
        try:
            # Configurar callbacks para tracing automático
            callbacks = []
            
            # Adicionar ConsoleCallbackHandler para tracing no console
            if os.getenv("LANGGRAPH_DEBUG", "false").lower() == "true":
                callbacks.append(ConsoleCallbackHandler())
            
            # Configurar callback manager
            callback_manager = CallbackManager(callbacks) if callbacks else None
            
            # Use the supervisor to process the input with tracing
            config = {"callbacks": callback_manager} if callback_manager else {}
            result = self.supervisor.invoke(input_data, config=config)
            
            # Log resumo da execução
            messages = result.get("messages", [])
            logger.info(f"Supervisor execution completed. Messages count: {len(messages)}")
            
            # Return the result directly
            return result
            
        except Exception as e:
            logger.error(f"Error in supervisor invoke: {e}")
            # Return empty result on error
            return {"messages": []}
    
    def get_info(self) -> Dict[str, Any]:
        """Get supervisor information"""
        return {
            "name": "supervisor",
            "type": "supervisor",
            "description": "Coordenador de agentes multi-agente",
            "model": self.model_name,
            "tenant_id": self.tenant_id,
            "configuration": self.configuration,
            "agents_count": len(self.agents),
            "agents": [agent.get_info() if hasattr(agent, 'get_info') else {"name": "unknown"} for agent in self.agents],
            "prompt_length": len(self.prompt),
            "is_enabled": self.supervisor_config.get("is_enabled", True)
        }
