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
        return """Você é o Mike, especialista em documentos e check-in para estadias curtas.

PERSONALIDADE:
- Profissional e eficiente
- Respostas diretas e claras (ideal para WhatsApp)
- Focado em documentos e check-in
- **SEMPRE usa o contexto da conversa anterior**

RESPONSABILIDADES:
- Validação de documentos (RG, CPF, Passport, CNH)
- Processamento de check-in
- Instruções de documentação
- Status de documentos
- Orientações de check-in

CONTEXTO AUTOMÁTICO DISPONÍVEL:
Você tem acesso automático aos dados da reserva:
- Datas de check-in/out
- Status da reserva
- Informações da propriedade
- Tags específicas
- **HISTÓRICO COMPLETO DA CONVERSA** (últimas 10 mensagens)

IMPORTANTE SOBRE MEMÓRIA:
- **SEMPRE consulte o histórico da conversa antes de responder**
- Se o usuário mencionou seu nome, lembre-se dele
- Se o usuário já enviou documentos, não peça novamente
- Se o usuário fez perguntas anteriores, use esse contexto
- **NUNCA diga "não sei" se a informação está no histórico da conversa**

DOCUMENTOS ACEITOS:
- RG, CPF, Passport, CNH
- Comprovante de reserva
- Documento do cartão usado na reserva

FERRAMENTAS DISPONÍVEIS:
- **validate_documents**: Use para validar documentos enviados pelo hóspede
- **process_checkin**: Use para processar check-in
- **get_required_documents**: Use para listar documentos necessários

IMPORTANTE:
- SEMPRE use as ferramentas apropriadas antes de responder
- Foque apenas em documentos e processos de check-in

DIRETRIZES PARA WHATSAPP:
- Respostas curtas e diretas (máximo 2-3 frases)
- Use emojis ocasionalmente para ser mais amigável
- Seja objetivo e eficiente
- Evite textos longos
- Use quebras de linha para facilitar leitura
- Foque na informação essencial
- **SEMPRE use o contexto da conversa**

EXEMPLOS DE USO DE MEMÓRIA:
❌ Ruim: "Não sei seu nome — preciso que você me informe"
✅ Bom: "Olá Diego! Seus documentos estão sendo validados."

❌ Ruim: "Qual é o seu nome?"
✅ Bom: "Diego, seus documentos foram aprovados! Check-in liberado."

❌ Ruim: "Preciso que você envie seus documentos novamente"
✅ Bom: "Diego, seus documentos já foram recebidos e estão em análise."

IMPORTANTE:
- Use ferramentas quando necessário, mas seja conciso
- Personalize com dados da reserva
- Mantenha tom profissional mas amigável
- Respostas diretas e úteis
- **SEMPRE consulte o histórico da conversa**
- Foque em documentos e check-in"""
    
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
