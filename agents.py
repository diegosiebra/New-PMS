"""
LangGraph Agent Manager
Manages agents and supervisor using separate agent files
Enhanced with state management for reservation data and conversation history
"""

import os
from typing import List, Dict, Any
from database import db_service
from mike_agent import MikeAgent
from lara_agent import LaraAgent
from supervisor_agent import SupervisorAgent
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage
import logging
from state_manager import state_manager, SupervisorState

logger = logging.getLogger(__name__)

class AgentManager:
    def __init__(self):
        self.agents = {}
        self.supervisors = {}
        self.agent_instances = {}
    
    def create_mike_agent(self, tenant_id: str, agent_config: Dict[str, Any]) -> MikeAgent:
        """Create Mike agent for document collection"""
        return MikeAgent(tenant_id, agent_config)
    
    def create_lara_agent(self, tenant_id: str, agent_config: Dict[str, Any]) -> LaraAgent:
        """Create Lara agent for RAG support"""
        return LaraAgent(tenant_id, agent_config)
    
    def create_supervisor_agent(self, tenant_id: str, agents: List[Any], supervisor_config: Dict[str, Any] = None) -> SupervisorAgent:
        """Create supervisor agent using langgraph-supervisor"""
        return SupervisorAgent(tenant_id, agents, supervisor_config)
    
    async def initialize_tenant_agents(self, tenant_id: str) -> bool:
        """Initialize agents for a tenant"""
        try:
            # Get agent configurations from database
            agent_configs = await db_service.get_agent_configurations(tenant_id)
            
            if not agent_configs:
                logger.warning(f"No agent configurations found for tenant {tenant_id}")
                return False
            
            agent_instances = []
            supervisor_config = None
            
            for config in agent_configs:
                if not config.get("is_enabled", False):
                    continue
                
                agent_type = config.get("agent_type")
                agent_name = config.get("agent_name", "").lower()
                
                if agent_type == "supervisor":
                    supervisor_config = config
                    logger.info(f"Found supervisor configuration for tenant {tenant_id}")
                
                elif agent_type == "document_collection" or agent_name == "mike":
                    agent_instance = self.create_mike_agent(tenant_id, config)
                    agent_instances.append(agent_instance)
                    logger.info(f"Created Mike agent for tenant {tenant_id}")
                
                elif agent_type == "rag_support" or agent_name == "lara":
                    agent_instance = self.create_lara_agent(tenant_id, config)
                    agent_instances.append(agent_instance)
                    logger.info(f"Created Lara agent for tenant {tenant_id}")
            
            if agent_instances:
                # Create supervisor with configuration from database
                supervisor_instance = self.create_supervisor_agent(tenant_id, agent_instances, supervisor_config)
                self.supervisors[tenant_id] = supervisor_instance.get_supervisor()
                self.agent_instances[tenant_id] = agent_instances

                logger.info(f"Initialized {len(agent_instances)} agents for tenant {tenant_id}")
                return True
            else:
                logger.warning(f"No enabled agents found for tenant {tenant_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error initializing agents for tenant {tenant_id}: {e}")
            return False
    
    async def process_message(self, tenant_id: str, message: str, whatsapp_number: str, conversation_id: str = None) -> Dict[str, Any]:
        """Process a message using the supervisor and agents with enhanced state"""
        try:
            if tenant_id not in self.supervisors:
                await self.initialize_tenant_agents(tenant_id)
            
            if tenant_id not in self.supervisors:
                return {
                    "success": False,
                    "message": "Agentes não disponíveis para este tenant",
                    "metadata": {"error": "No agents available"}
                }
            
            supervisor = self.supervisors[tenant_id]
            
            # Load comprehensive state data
            logger.info(f"Loading state data for tenant {tenant_id}, WhatsApp {whatsapp_number}")
            state_data = await state_manager.load_state_data(tenant_id, whatsapp_number, conversation_id)
            
            # Create enhanced state for LangGraph
            enhanced_state = state_manager.create_initial_state(tenant_id, whatsapp_number, message, state_data)
            
            # State is now automatically injected by LangGraph using InjectedState
            
            # Log state information
            reservations_count = len(enhanced_state.get("reservations", []))
            history_count = len(enhanced_state.get("conversation_history", []))
            logger.info(f"State loaded: {reservations_count} reservations, {history_count} messages")
            
            # Process with supervisor using enhanced state
            result = supervisor.invoke(enhanced_state)
            
            # Extract response from the MessagesState - formato simples
            messages = result.get("messages", [])
            
            # Pegar a última AIMessage do supervisor (que já inclui a resposta do agente executado)
            from langchain_core.messages import AIMessage
            ai_messages = [msg for msg in messages if isinstance(msg, AIMessage)]
            
            if ai_messages:
                # A última mensagem já contém a resposta completa do agente executado
                response_message = ai_messages[-1].content
                logger.info(f"Supervisor completed execution with response length: {len(response_message)}")
                
                # Log detalhado para debug
                logger.info(f"Total messages: {len(messages)}")
                logger.info(f"AI messages count: {len(ai_messages)}")
                for i, msg in enumerate(ai_messages):
                    logger.info(f"AI Message {i}: {msg.content[:100]}...")
            else:
                response_message = "Desculpe, não consegui processar sua mensagem."
            
            # Log execution with enhanced metadata
            await db_service.log_agent_execution({
                "tenant_id": tenant_id,
                "conversation_id": whatsapp_number,
                "agent_type": "supervisor",
                "agent_name": "Supervisor",
                "input": {"message": message},
                "output": {"response": response_message},
                "status": "success",
                "execution_time": None,
                "error_message": None,
                "created_at": "now()"
            })
            
            return {
                "success": True,
                "message": response_message,
                "metadata": {
                    "tenant_id": tenant_id,
                    "conversation_id": conversation_id or whatsapp_number,
                    "whatsapp_number": whatsapp_number,
                    "reservations_count": reservations_count,
                    "history_count": history_count,
                    "timestamp": "now()",
                    "state_context": state_manager.format_state_for_agents(enhanced_state)[:200] + "..." if len(state_manager.format_state_for_agents(enhanced_state)) > 200 else state_manager.format_state_for_agents(enhanced_state)
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing message for tenant {tenant_id}: {e}")
            
            # Log error
            await db_service.log_agent_execution({
                "tenant_id": tenant_id,
                "conversation_id": whatsapp_number,  # Always use WhatsApp number as conversation_id
                "agent_type": "supervisor",
                "agent_name": "Supervisor",
                "input": {"message": message},
                "output": None,
                "status": "error",
                "execution_time": None,
                "error_message": str(e),
                "created_at": "now()"
            })
            
            return {
                "success": False,
                "message": "Erro interno do sistema. Tente novamente.",
                "metadata": {
                    "error": str(e),
                    "tenant_id": tenant_id,
                    "timestamp": "now()"
                }
            }
    
    def get_agent_info(self, tenant_id: str) -> Dict[str, Any]:
        """Get information about agents for a tenant"""
        if tenant_id not in self.agent_instances:
            return {"agents": [], "supervisor": None}
        
        agents_info = []
        for agent_instance in self.agent_instances[tenant_id]:
            if hasattr(agent_instance, 'get_info'):
                agents_info.append(agent_instance.get_info())
        
        supervisor_info = None
        if tenant_id in self.supervisors:
            supervisor_info = {
                "available": True,
                "agents_count": len(self.agent_instances[tenant_id])
            }
        
        return {
            "agents": agents_info,
            "supervisor": supervisor_info
        }
    
    def reload_tenant_agents(self, tenant_id: str) -> bool:
        """Reload agents for a tenant"""
        try:
            # Clear existing agents
            if tenant_id in self.agent_instances:
                del self.agent_instances[tenant_id]
            if tenant_id in self.supervisors:
                del self.supervisors[tenant_id]
            
            logger.info(f"Cleared existing agents for tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error reloading agents for tenant {tenant_id}: {e}")
            return False

# Global agent manager instance
agent_manager = AgentManager()