"""
Mike Agent - Document Collection Specialist
Specialized in document validation and check-in processes for short-stays
All configurations loaded from database
Enhanced with state access for reservation and conversation context
"""

import os
import json
from typing import Dict, Any, List, Callable
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
import logging
from state_manager import state_manager, SupervisorState

logger = logging.getLogger(__name__)

class MikeAgent:
    """Mike Agent for document collection and check-in processes"""
    
    def __init__(self, tenant_id: str, agent_config: Dict[str, Any]):
        self.tenant_id = tenant_id
        self.agent_config = agent_config
        self.model_name = agent_config.get("model", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
        self.configuration = agent_config.get("configuration", {})
        self.prompt = agent_config.get("prompt", self._get_default_prompt())
        self.tools_config = agent_config.get("tools", [])
        
        # Configure temperature from database or default
        temperature = self.configuration.get("temperature", 0.3)
        self.model = ChatOpenAI(model=self.model_name, temperature=temperature)
        self.agent = None
        self._create_agent()
    
    def _create_agent(self):
        """Create the Mike agent with tools and prompt from database configuration"""
        
        # Create tools based on database configuration
        tools = self._create_tools_from_config()
        
        # Create the agent
        self.agent = create_react_agent(
            model=self.model,
            tools=tools,
            prompt=self.prompt,
            name="mike",
            state_schema=SupervisorState
        )
        
        logger.info(f"Mike agent created for tenant {self.tenant_id} with {len(tools)} tools")
    
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
            
            if tool_name == "validate_document":
                tools.append(self._create_validate_document_tool(tool_config))
            elif tool_name == "register_document":
                tools.append(self._create_register_document_tool(tool_config))
            else:
                logger.warning(f"Unknown tool: {tool_name}")
        
        return tools
    
    def _create_validate_document_tool(self, tool_config: Dict[str, Any]) -> Callable:
        """Create validate_document tool from configuration with state access"""
        
        def validate_document(is_legible: bool, is_complete: bool, document_type: str, document_number: str, state: Dict[str, Any] = None) -> str:
            """Validate if a document is legible and complete
            
            Args:
                is_legible: Whether the document is legible
                is_complete: Whether the document is complete
                document_type: Type of document (RG, CPF, CNH, Passaporte)
                document_number: Document number
                state: Current conversation state with reservation context
                
            Returns:
                Validation result message
            """
            logger.info(f"Mike: Validating {document_type} document - Legible: {is_legible}, Complete: {is_complete}")
            
            # Get reservation context if available
            context_info = ""
            if state and state.get("reservations"):
                reservations = state["reservations"]
                if reservations:
                    latest_reservation = reservations[0]
                    if latest_reservation.get("reservation_id"):
                        context_info = f" para a reserva {latest_reservation['reservation_id']}"
            
            if not is_legible:
                return f"❌ Documento {document_type} não está legível{context_info}. Por favor, envie uma foto mais clara."
            
            if not is_complete:
                return f"❌ Documento {document_type} está incompleto{context_info}. Por favor, envie o documento completo."
            
            if document_type not in ["RG", "CPF", "CNH", "Passaporte"]:
                return f"❌ Tipo de documento {document_type} não aceito. Tipos aceitos: RG, CPF, CNH, Passaporte."
            
            return f"✅ Documento {document_type} validado com sucesso{context_info}! Número: {document_number[:10]}..."
        
        return validate_document
    
    def _create_register_document_tool(self, tool_config: Dict[str, Any]) -> Callable:
        """Create register_document tool from configuration"""
        
        def register_document(guest_id: str, document_data: Dict[str, Any], document_type: str, document_number: str) -> str:
            """Register a document in the system
            
            Args:
                guest_id: Guest identifier
                document_data: Document data
                document_type: Type of document
                document_number: Document number
                
            Returns:
                Registration result message
            """
            logger.info(f"Mike: Registering {document_type} document for guest {guest_id}")
            
            # Simulate document registration
            return f"✅ Documento {document_type} registrado com sucesso para o hóspede {guest_id}. Número: {document_number[:10]}..."
        
        return register_document
    
    def _get_default_tools(self) -> List[Callable]:
        """Get default tools when no configuration is available"""
        
        def validate_documents(document_type: str, document_data: str) -> str:
            """Validate documents for check-in process"""
            logger.info(f"Mike: Validating {document_type} document")
            
            if document_type.lower() in ["rg", "cpf", "passport", "cnh"]:
                return f"✅ Documento {document_type} validado com sucesso. Dados: {document_data[:50]}..."
            else:
                return f"⚠️ Tipo de documento {document_type} não reconhecido. Tipos aceitos: RG, CPF, Passport, CNH"
        
        def process_checkin(guest_name: str, reservation_id: str) -> str:
            """Process guest check-in"""
            logger.info(f"Mike: Processing check-in for {guest_name}")
            return f"✅ Check-in processado com sucesso para {guest_name} (Reserva: {reservation_id}). Hóspede pode acessar a propriedade."
        
        def get_required_documents() -> str:
            """Get list of required documents for check-in"""
            logger.info("Mike: Providing required documents list")
            return """📋 Documentos necessários para check-in:
            
1. **Identidade**: RG, CPF ou Passport válido
2. **Comprovante de reserva**: Confirmação da reserva
3. **Documento do cartão**: Cartão usado na reserva (para verificação)
4. **Autorização**: Se não for o titular da reserva

⚠️ Todos os documentos devem estar legíveis e válidos."""
        
        return [validate_documents, process_checkin, get_required_documents]
    
    def _get_default_prompt(self) -> str:
        """Get default prompt when no configuration is available"""
        return """Você é o Mike, especialista em documentos e check-in para estadias curtas (short-stays).

🎯 SUAS RESPONSABILIDADES:
- Coletar e validar documentos necessários para check-in
- Processar o check-in de hóspedes
- Orientar sobre documentos obrigatórios
- Verificar status de documentos
- Fornecer instruções de check-in

📋 DOCUMENTOS ACEITOS:
- RG, CPF, Passport, CNH
- Comprovante de reserva
- Documento do cartão usado na reserva

🏠 CONTEXTO DISPONÍVEL:
Você tem acesso a informações importantes do hóspede:
- Dados da reserva (check-in, check-out, status)
- Histórico da conversa
- Informações do WhatsApp e tenant

Use essas informações para:
- Personalizar suas respostas
- Referenciar detalhes específicos da reserva
- Considerar o contexto da conversa anterior
- Fornecer orientações mais precisas

⚠️ REGRAS IMPORTANTES:
- Sempre seja prestativo e eficiente
- Valide documentos antes de processar check-in
- Forneça instruções claras e detalhadas
- Use o contexto da reserva para personalizar respostas
- Mantenha o foco na documentação e check-in
- Seja paciente com hóspedes que têm dúvidas

IMPORTANTE: Use sempre o contexto disponível para fornecer respostas personalizadas e relevantes. Referencie a reserva específica quando apropriado."""
    
    def get_agent(self):
        """Get the created agent"""
        return self.agent
    
    def get_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "name": "mike",
            "type": "document_collection",
            "description": "Especialista em documentos e check-in",
            "model": self.model_name,
            "tenant_id": self.tenant_id,
            "configuration": self.configuration,
            "tools_count": len(self.tools_config) if self.tools_config else 3,
            "tools": [tool.get("name") for tool in self.tools_config] if self.tools_config else ["validate_documents", "process_checkin", "get_required_documents"],
            "prompt_length": len(self.prompt),
            "is_enabled": self.agent_config.get("is_enabled", True)
        }
