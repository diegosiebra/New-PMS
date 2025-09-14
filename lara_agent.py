"""
Lara Agent - RAG Support Specialist
Specialized in general support and property information for short-stays
All configurations loaded from database
"""

import os
import json
from typing import Dict, Any, List, Callable
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
import logging

logger = logging.getLogger(__name__)

class LaraAgent:
    """A Lara é uma atendente especializada em responder dúvidas sobre a reserva do usuário, além de fornecer dicas e procedimentos úteis para estadias."""
    
    def __init__(self, tenant_id: str, agent_config: Dict[str, Any]):
        self.tenant_id = tenant_id
        self.agent_config = agent_config
        self.model_name = agent_config.get("model", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
        self.configuration = agent_config.get("configuration", {})
        self.prompt = agent_config.get("prompt", self._get_default_prompt())
        self.tools_config = agent_config.get("tools", [])
        self.model = ChatOpenAI(model=self.model_name, temperature=1)
        self.agent = None
        self._create_agent()
    
    def _create_agent(self):
        """Create the Lara agent with tools and prompt from database configuration"""
        
        # Create tools based on database configuration
        tools = self._create_tools_from_config()
        
        # Create the agent
        self.agent = create_react_agent(
            model=self.model,
            tools=tools,
            prompt=self.prompt,
            name="lara"
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
    
    def _create_search_knowledge_base_tool(self, tool_config: Dict[str, Any]) -> Callable:
        """Create search_knowledge_base tool from configuration"""
        
        def search_knowledge_base(query: str, category: str = "general", limit: int = 5) -> str:
            """Search information in the knowledge base
            
            Args:
                query: Search query
                category: Category to search in (services, policies, amenities, location, general)
                limit: Maximum number of results
                
            Returns:
                Search results from knowledge base
            """
            logger.info(f"Lara: Searching knowledge base for '{query}' in category '{category}'")
            
            # Simulate knowledge base search
            knowledge_base = {
                "services": {
                    "wifi": "WiFi gratuito disponível em toda a propriedade. Senha: PROP2024",
                    "limpeza": "Serviço de limpeza disponível mediante solicitação",
                    "concierge": "Concierge 24h para assistência"
                },
                "policies": {
                    "checkin": "Check-in a partir das 15h",
                    "checkout": "Check-out até 11h",
                    "fumantes": "Proibido fumar em qualquer área da propriedade"
                },
                "amenities": {
                    "cozinha": "Cozinha totalmente equipada com utensílios básicos",
                    "lavanderia": "Máquina de lavar e secadora disponíveis",
                    "estacionamento": "1 vaga de estacionamento coberta"
                },
                "location": {
                    "centro": "Localizada no centro da cidade",
                    "transporte": "Próximo ao metrô e pontos de ônibus",
                    "comercio": "Supermercado e farmácia a 5 minutos a pé"
                }
            }
            
            category_data = knowledge_base.get(category, {})
            results = []
            
            for key, value in category_data.items():
                if query.lower() in key.lower() or query.lower() in value.lower():
                    results.append(f"• {key.title()}: {value}")
            
            if results:
                return f"📚 Resultados da busca por '{query}':\n\n" + "\n".join(results[:limit])
            else:
                return f"ℹ️ Nenhum resultado encontrado para '{query}' na categoria '{category}'. Tente uma busca mais específica."
        
        return search_knowledge_base
    
    def _create_get_reservation_data_tool(self, tool_config: Dict[str, Any]) -> Callable:
        """Create get_reservation_data tool from configuration"""
        
        def get_reservation_data(reservation_id: str, data_type: str = "details", guest_id: str = None) -> str:
            """Get specific reservation data for the client
            
            Args:
                reservation_id: Reservation identifier
                data_type: Type of data (details, services, billing, amenities)
                guest_id: Guest identifier
                
            Returns:
                Reservation data
            """
            logger.info(f"Lara: Getting reservation data for {reservation_id}, type: {data_type}")
            
            # Simulate reservation data retrieval
            reservation_data = {
                "details": f"Reserva {reservation_id}: Check-in 15h, Check-out 11h, 2 quartos",
                "services": "WiFi gratuito, Limpeza, Concierge 24h",
                "billing": "Pagamento confirmado, sem taxas adicionais",
                "amenities": "Cozinha equipada, Lavanderia, Estacionamento"
            }
            
            return f"📋 Dados da reserva {reservation_id}:\n\n{reservation_data.get(data_type, 'Tipo de dados não encontrado')}"
        
        return get_reservation_data
    
    def _create_escalate_to_human_tool(self, tool_config: Dict[str, Any]) -> Callable:
        """Create escalate_to_human tool from configuration"""
        
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
    
    def _get_default_tools(self) -> List[Callable]:
        """Get default tools when no configuration is available"""
        
        def get_property_info(query: str) -> str:
            """Get information about the property"""
            logger.info(f"Lara: Getting property info for query: {query}")
            
            property_info = {
                "localização": "Centro da cidade, próximo ao metrô",
                "capacidade": "Até 4 pessoas",
                "quartos": "2 quartos, 1 banheiro",
                "amenidades": "WiFi, Ar condicionado, Cozinha equipada, Estacionamento",
                "check-in": "A partir das 15h",
                "check-out": "Até 11h"
            }
            
            if "localização" in query.lower() or "onde" in query.lower():
                return f"📍 Localização: {property_info['localização']}"
            elif "capacidade" in query.lower() or "pessoas" in query.lower():
                return f"👥 Capacidade: {property_info['capacidade']}"
            elif "quarto" in query.lower() or "banheiro" in query.lower():
                return f"🏠 Quartos: {property_info['quartos']}"
            else:
                return f"🏡 Informações da propriedade:\n- Localização: {property_info['localização']}\n- Capacidade: {property_info['capacidade']}\n- Quartos: {property_info['quartos']}\n- Amenidades: {property_info['amenidades']}"
        
        def get_house_rules() -> str:
            """Get house rules and policies"""
            logger.info("Lara: Providing house rules")
            
            return """📋 Regras da Casa:
            
🕐 **Horários:**
- Check-in: A partir das 15h
- Check-out: Até 11h
- Silêncio: Após 22h

🚫 **Proibições:**
- Fumar em qualquer área
- Animais de estimação
- Festas ou eventos
- Barulho excessivo

✅ **Permitido:**
- Uso da cozinha
- Lavanderia
- Estacionamento
- WiFi gratuito

⚠️ **Importante:** Respeite os vizinhos e mantenha a propriedade limpa."""
        
        def get_amenities() -> str:
            """Get available amenities"""
            logger.info("Lara: Providing amenities information")
            
            return """🏡 Amenidades Disponíveis:
            
📶 **Conectividade:**
- WiFi gratuito (senha no manual)
- Internet de alta velocidade

🌡️ **Conforto:**
- Ar condicionado em todos os ambientes
- Aquecimento central
- Ventiladores de teto

🍳 **Cozinha:**
- Fogão e forno
- Geladeira
- Microondas
- Utensílios básicos
- Cafeteira

🚗 **Estacionamento:**
- 1 vaga coberta
- Acesso direto

🧺 **Lavanderia:**
- Máquina de lavar
- Secadora
- Ferro de passar

📺 **Entretenimento:**
- TV Smart
- Netflix
- Jogos de tabuleiro"""
        
        return [get_property_info, get_house_rules, get_amenities]
    
    def _get_default_prompt(self) -> str:
        """Get default prompt when no configuration is available"""
        return """Você é a Lara, especialista em suporte geral com conhecimento sobre estadias curtas (short-stays).

🎯 SUAS RESPONSABILIDADES:
- Responder perguntas gerais sobre a propriedade
- Fornecer informações sobre regras da casa
- Ajudar com questões de hospedagem
- Orientar sobre serviços disponíveis
- Dar recomendações locais
- Suporte geral aos hóspedes

📋 ÁREAS DE ESPECIALIDADE:
- Informações da propriedade
- Regras da casa e políticas
- Amenidades disponíveis
- Recomendações locais
- Suporte técnico geral
- Orientações de uso

⚠️ REGRAS IMPORTANTES:
- Seja sempre prestativa e informativa
- Ofereça uma experiência excelente ao hóspede
- Se a pergunta for sobre documentos/check-in, oriente para falar com o Mike
- Mantenha o foco em suporte geral e informações
- Seja paciente e detalhada nas explicações

IMPORTANTE: Seja sempre prestativa e informativa, oferecendo uma experiência excelente ao hóspede. Foque em suporte geral e informações sobre a propriedade."""
    
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
