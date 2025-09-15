"""
Lara Agent - RAG Support Specialist
Specialized in general support and property information for short-stays
All configurations loaded from database
Enhanced with state access for reservation and conversation context
"""

import os
import json
from typing import Dict, Any, List, Callable, Annotated
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent, InjectedState
from langchain_core.tools import tool
import logging
from state_manager import state_manager, SupervisorState
from rag_service import rag_service

logger = logging.getLogger(__name__)

# No need for global state - using InjectedState from LangGraph

class LaraAgent:
    """A Lara é uma atendente especializada em responder dúvidas sobre a reserva do usuário, além de fornecer dicas e procedimentos úteis para estadias."""
    
    def __init__(self, tenant_id: str, agent_config: Dict[str, Any]):
        self.tenant_id = tenant_id
        self.agent_config = agent_config
        self.model_name = agent_config.get("model", os.getenv("OPENAI_MODEL", "gpt-5-mini"))
        self.configuration = agent_config.get("configuration", {})
        self.prompt = agent_config.get("prompt", "")
        if not self.prompt:
            raise ValueError("Lara agent prompt is required and must be configured in database")
        self.tools_config = agent_config.get("tools", [])
        
        # Configure temperature from database or default
        temperature = self.configuration.get("temperature", 0.7)
        self.model = ChatOpenAI(model=self.model_name, temperature=temperature)
        self.agent = None
        self._create_agent()
    
    def _create_agent(self):
        """Create the Lara agent with tools and prompt from database configuration"""
        
        # Create tools based on database configuration
        tools = self._create_tools_from_config()
        
        # Create the agent with SupervisorState to access full state
        self.agent = create_react_agent(
            model=self.model,
            tools=tools,
            prompt=self.prompt,
            name="lara",
            state_schema=SupervisorState
        )
        
        logger.info(f"Lara agent created for tenant {self.tenant_id} with {len(tools)} tools")
    
    def _create_tools_from_config(self) -> List[Callable]:
        """Create tools based on database configuration"""
        tools = []
        
        # Default tools if no tools configured in database
        if not self.tools_config:
            logger.info("No tools configured in database, using default tools")
            return self._get_default_tools()
        
        # Create tools from database configuration
        for tool_config in self.tools_config:
            tool_name = tool_config.get("name")
            tool_description = tool_config.get("description", "")
            
            if tool_name == "search_knowledge_base":
                tools.append(self._create_search_knowledge_base_tool(tool_config))
            elif tool_name == "get_reservation_data":
                tools.append(self._create_get_reservation_data_tool(tool_config))
            elif tool_name == "escalate_to_human":
                tools.append(self._create_escalate_to_human_tool(tool_config))
            else:
                logger.warning(f"Unknown tool: {tool_name}")
        
        return tools
    
    def _get_default_tools(self) -> List[Callable]:
        """Get default tools when no configuration is available"""
        logger.info("Creating default tools for Lara agent")
        
        # Create default tool configurations
        default_tools = [
            {
                "name": "search_knowledge_base",
                "description": "Search information in the knowledge base using RAG"
            },
            {
                "name": "get_reservation_data", 
                "description": "Get specific reservation data for the client"
            },
            {
                "name": "escalate_to_human",
                "description": "Escalate the conversation to human support"
            }
        ]
        
        tools = []
        for tool_config in default_tools:
            tool_name = tool_config.get("name")
            
            if tool_name == "search_knowledge_base":
                tools.append(self._create_search_knowledge_base_tool(tool_config))
            elif tool_name == "get_reservation_data":
                tools.append(self._create_get_reservation_data_tool(tool_config))
            elif tool_name == "escalate_to_human":
                tools.append(self._create_escalate_to_human_tool(tool_config))
        
        return tools
    
    def _create_search_knowledge_base_tool(self, tool_config: Dict[str, Any]) -> Callable:
        """Create search_knowledge_base tool from configuration with RAG integration"""
        
        @tool
        def search_knowledge_base(
            query: str, 
            category: str = "general", 
            limit: int = 5,
            state: Annotated[SupervisorState, InjectedState] = None
        ) -> str:
            """Search information in the knowledge base using RAG with reservation context
            
            Args:
                query: Search query
                category: Category to search in (services, policies, amenities, location, general)
                limit: Maximum number of results
                state: Current conversation state with reservation context (injected automatically)
                
            Returns:
                Search results from knowledge base
            """
            logger.info(f"Lara: Searching knowledge base for '{query}' in category '{category}'")
            
            try:
                # Extract reservation context from injected state
                reservation = None
                if state and state.get("reservations"):
                    reservations = state["reservations"]
                    if reservations:
                        reservation = reservations[0]  # Use latest reservation
                
                # Search documents using RAG
                import asyncio
                documents = asyncio.run(rag_service.search_documents(query, reservation, limit))
                
                if documents:
                    # Format documents for response
                    return rag_service.format_documents_for_response(documents, query)
                else:
                    return f"ℹ️ Nenhuma informação encontrada sobre '{query}' na base de conhecimento."
                    
            except Exception as e:
                logger.error(f"Error in RAG search: {e}")
                return f"❌ Erro ao buscar informações sobre '{query}': {str(e)}"
        
        return search_knowledge_base
    
    def _create_get_reservation_data_tool(self, tool_config: Dict[str, Any]) -> Callable:
        """Create get_reservation_data tool from configuration with state access"""
        
        @tool
        def get_reservation_data(
            reservation_id: str = None, 
            data_type: str = "details", 
            guest_id: str = None,
            state: Annotated[SupervisorState, InjectedState] = None
        ) -> str:
            """Get specific reservation data for the client
            
            Args:
                reservation_id: Reservation identifier (optional if using state)
                data_type: Type of data (details, services, billing, amenities)
                guest_id: Guest identifier
                state: Current conversation state with reservation context (injected automatically)
                
            Returns:
                Reservation data
            """
            logger.info(f"Lara: Getting reservation data for {reservation_id}, type: {data_type}")
            
            # Try to get reservation from injected state first
            if state and state.get("reservations"):
                reservations = state["reservations"]
                target_reservation = None
                
                if reservation_id:
                    # Find specific reservation by ID
                    target_reservation = next((r for r in reservations if r.get("reservation_id") == reservation_id), None)
                else:
                    # Use first/latest reservation
                    target_reservation = reservations[0] if reservations else None
                
                if target_reservation:
                    if data_type == "details":
                        details = []
                        if target_reservation.get("reservation_id"):
                            details.append(f"ID: {target_reservation['reservation_id']}")
                        if target_reservation.get("checkin_date"):
                            details.append(f"Check-in: {target_reservation['checkin_date']} {target_reservation.get('checkin_time', '')}")
                        if target_reservation.get("checkout_date"):
                            details.append(f"Check-out: {target_reservation['checkout_date']} {target_reservation.get('checkout_time', '')}")
                        if target_reservation.get("status"):
                            details.append(f"Status: {target_reservation['status']}")
                        if target_reservation.get("listing_id"):
                            details.append(f"Propriedade: {target_reservation['listing_id']}")
                        
                        return f"📋 Detalhes da Reserva:\n\n" + "\n".join(details)
                    
                    elif data_type == "services":
                        # Search for services information using RAG
                        try:
                            from database import db_service
                            scope_tags = self._extract_scope_tags(target_reservation)
                            import asyncio
                            services_docs = asyncio.run(db_service.search_documents_rag("serviços inclusos", scope_tags, 3))
                            
                            if services_docs:
                                services_info = []
                                for doc in services_docs:
                                    content = doc.get("content", "")
                                    services_info.append(content[:200] + "..." if len(content) > 200 else content)
                                return f"🔧 Serviços Inclusos:\n\n" + "\n\n".join(services_info)
                        except Exception as e:
                            logger.error(f"Error searching services: {e}")
                        
                        return f"❌ Erro ao buscar informações de serviços: {str(e)}"
                    
                    elif data_type == "billing":
                        # Search for billing information using RAG
                        try:
                            from database import db_service
                            scope_tags = self._extract_scope_tags(target_reservation)
                            billing_docs = asyncio.run(db_service.search_documents_rag("pagamento cobrança fatura", scope_tags, 3))
                            
                            if billing_docs:
                                billing_info = []
                                for doc in billing_docs:
                                    content = doc.get("content", "")
                                    billing_info.append(content[:200] + "..." if len(content) > 200 else content)
                                return f"💰 Informações de Pagamento:\n\n" + "\n\n".join(billing_info)
                        except Exception as e:
                            logger.error(f"Error searching billing: {e}")
                        
                        return f"❌ Erro ao buscar informações de pagamento: {str(e)}"
                    
                    elif data_type == "amenities":
                        # Search for amenities information using RAG
                        try:
                            from database import db_service
                            scope_tags = self._extract_scope_tags(target_reservation)
                            amenities_docs = asyncio.run(db_service.search_documents_rag("amenidades comodidades facilidades", scope_tags, 3))
                            
                            if amenities_docs:
                                amenities_info = []
                                for doc in amenities_docs:
                                    content = doc.get("content", "")
                                    amenities_info.append(content[:200] + "..." if len(content) > 200 else content)
                                return f"🏡 Amenidades:\n\n" + "\n\n".join(amenities_info)
                        except Exception as e:
                            logger.error(f"Error searching amenities: {e}")
                        
                        return f"❌ Erro ao buscar informações de amenidades: {str(e)}"
            
            return f"❌ Reserva {reservation_id or 'atual'} não encontrada no estado atual."
        
        return get_reservation_data
    
    def _extract_scope_tags(self, reservation: Dict[str, Any]) -> List[str]:
        """Extract scope tags from reservation for RAG search"""
        scope_tags = ["GLOBAL"]  # Default scope
        
        if reservation:
            reservation_tags = reservation.get("tags", {})
            
            # Extract relevant tags for scope
            if isinstance(reservation_tags, dict):
                # Extract building and apartment codes
                building_code = reservation_tags.get("buildingCode")
                apartment_code = reservation_tags.get("apartmentCode")
                
                if building_code:
                    scope_tags.append(building_code)
                if apartment_code:
                    scope_tags.append(apartment_code)
                
                # Add any other relevant tags
                for key, value in reservation_tags.items():
                    if key not in ["buildingCode", "apartmentCode"] and isinstance(value, str):
                        scope_tags.append(value)
        
        # Remove duplicates and ensure we have at least GLOBAL
        return list(set(scope_tags))
    
    def _create_escalate_to_human_tool(self, tool_config: Dict[str, Any]) -> Callable:
        """Create escalate_to_human tool from configuration"""
        
        @tool
        def escalate_to_human(reason: str, context: str, priority: str = "medium") -> str:
            """Escalate the conversation to human support
            
            Args:
                reason: Reason for escalation
                context: Context of the conversation
                priority: Priority level (low, medium, high, urgent)
                
            Returns:
                Escalation confirmation
            """
            logger.info(f"Lara: Escalating to human support - Reason: {reason}, Priority: {priority}")
            
            priority_emoji = {
                "low": "🟢",
                "medium": "🟡", 
                "high": "🟠",
                "urgent": "🔴"
            }
            
            emoji = priority_emoji.get(priority, "🟡")
            
            return f"{emoji} Sua solicitação foi escalada para atendimento humano.\n\n**Motivo:** {reason}\n**Prioridade:** {priority.title()}\n\nUm atendente entrará em contato em breve. Obrigada pela paciência!"
        
        return escalate_to_human
    
    def get_agent(self):
        """Get the created agent"""
        return self.agent
    
    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": "lara",
            "type": "rag_support",
            "description": "Especialista em suporte geral e informações",
            "model": self.model_name,
            "tenant_id": self.tenant_id,
            "configuration": self.configuration,
            "tools_count": len(self.tools_config) if self.tools_config else 3,
            "tools": [tool.get("name") for tool in self.tools_config] if self.tools_config else ["get_property_info", "get_house_rules", "get_amenities"],
            "prompt_length": len(self.prompt),
            "is_enabled": self.agent_config.get("is_enabled", True)
        }
