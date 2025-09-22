"""
Mike Agent - Document Collection Specialist
Specialized in document validation and check-in processes for short-stays
All configurations loaded from database
Enhanced with state access for reservation and conversation context
"""

import os
import json
import hashlib
import base64
from typing import Dict, Any, List, Callable, Optional
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
import logging
from state_manager import state_manager, SupervisorState
from database import db_service
from models import IDDocument

logger = logging.getLogger(__name__)

class MikeAgent:
    """Mike Agent for document collection and check-in processes"""
    
    def __init__(self, tenant_id: str, agent_config: Dict[str, Any]):
        self.tenant_id = tenant_id
        self.agent_config = agent_config
        self.model_name = agent_config.get("model", os.getenv("OPENAI_MODEL", "gpt-5-mini"))
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
            elif tool_name == "store_document":
                tools.append(self._create_store_document_tool(tool_config))
            elif tool_name == "extract_name_from_document":
                tools.append(self._create_extract_name_tool(tool_config))
            elif tool_name == "check_document_status":
                tools.append(self._create_check_document_status_tool(tool_config))
            elif tool_name == "list_required_documents":
                tools.append(self._create_list_required_documents_tool(tool_config))
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
    
    def _create_store_document_tool(self, tool_config: Dict[str, Any]) -> Callable:
        """Create store_document tool from configuration"""
        
        async def store_document(
            document_type: str, 
            base64_data: str, 
            file_name: str,
            mime_type: str,
            guest_id: Optional[int] = None,
            reservation_id: Optional[str] = None,
            state: Dict[str, Any] = None
        ) -> str:
            """Store a document in the iddocuments table
            
            Args:
                document_type: Type of document (RG, CPF, CNH, Passport)
                base64_data: Base64 encoded document data
                file_name: Original file name
                mime_type: MIME type of the file
                guest_id: Guest ID (optional)
                reservation_id: Reservation ID (links to Reservations.reservationid)
                state: Current conversation state
                
            Returns:
                Storage result message
            """
            logger.info(f"Mike: Storing {document_type} document")
            
            try:
                # Get tenant_id from state
                tenant_id = state.get("tenant_id") if state else self.tenant_id
                
                # Generate file hash for deduplication
                file_hash = hashlib.sha256(base64_data.encode()).hexdigest()
                
                # Create storage path
                storage_path = f"documents/{tenant_id}/{document_type}/{file_hash[:8]}_{file_name}"
                
                # Prepare document data
                document_data = {
                    "tenant_id": tenant_id,
                    "reservation_id": reservation_id,
                    "guest_id": guest_id,
                    "type": document_type,
                    "storage_path": storage_path,
                    "file_size": len(base64_data),
                    "mime_type": mime_type,
                    "hash": file_hash,
                    "base64_data": base64_data,
                    "status": "pending",
                    "validation_status": "pending",
                    "processing_metadata": {
                        "file_name": file_name,
                        "uploaded_by": "mike_agent",
                        "conversation_id": state.get("conversation_id") if state else None
                    }
                }
                
                # Store document in database
                document_id = await db_service.store_document(document_data)
                
                if document_id:
                    return f"✅ Documento {document_type} armazenado com sucesso! ID: {document_id}"
                else:
                    return f"❌ Erro ao armazenar documento {document_type}"
                    
            except Exception as e:
                logger.error(f"Error storing document: {e}")
                return f"❌ Erro interno ao armazenar documento {document_type}: {str(e)}"
        
        return store_document
    
    def _create_extract_name_tool(self, tool_config: Dict[str, Any]) -> Callable:
        """Create extract_name_from_document tool from configuration"""
        
        async def extract_name_from_document(
            document_id: int,
            document_type: str,
            base64_data: Optional[str] = None,
            state: Dict[str, Any] = None
        ) -> str:
            """Extract person name from document using OCR/AI
            
            Args:
                document_id: Document ID in database
                document_type: Type of document
                base64_data: Base64 data (if not provided, will fetch from DB)
                state: Current conversation state
                
            Returns:
                Extraction result with person name
            """
            logger.info(f"Mike: Extracting name from {document_type} document {document_id}")
            
            try:
                # If base64_data not provided, fetch from database
                if not base64_data:
                    document = await db_service.get_document_by_id(document_id)
                    if not document:
                        return f"❌ Documento {document_id} não encontrado"
                    base64_data = document.get("base64_data")
                
                if not base64_data:
                    return f"❌ Dados do documento {document_id} não disponíveis"
                
                # Simulate name extraction (in real implementation, use OCR/AI service)
                extracted_name = await self._simulate_name_extraction(document_type, base64_data)
                
                # Update document with extracted name
                await db_service.update_document_status(
                    document_id, 
                    "approved", 
                    "validated",
                    {"extracted_name": extracted_name, "extraction_method": "ai_simulation"}
                )
                
                if extracted_name:
                    return f"✅ Nome extraído do documento {document_type}: {extracted_name}"
                else:
                    return f"⚠️ Não foi possível extrair o nome do documento {document_type}. Verificação manual necessária."
                    
            except Exception as e:
                logger.error(f"Error extracting name from document: {e}")
                return f"❌ Erro ao extrair nome do documento: {str(e)}"
        
        return extract_name_from_document
    
    def _create_check_document_status_tool(self, tool_config: Dict[str, Any]) -> Callable:
        """Create check_document_status tool from configuration"""
        
        async def check_document_status(
            document_type: str,
            guest_id: Optional[int] = None,
            reservation_id: Optional[str] = None,
            state: Dict[str, Any] = None
        ) -> str:
            """Check if a document has already been submitted
            
            Args:
                document_type: Type of document to check
                guest_id: Guest ID (optional)
                reservation_id: Reservation ID (optional)
                state: Current conversation state
                
            Returns:
                Status check result
            """
            logger.info(f"Mike: Checking status for {document_type} document")
            
            try:
                tenant_id = state.get("tenant_id") if state else self.tenant_id
                
                # Check if document exists
                exists = await db_service.check_document_exists(
                    tenant_id, document_type, guest_id=guest_id, reservation_id=reservation_id
                )
                
                if exists:
                    return f"✅ Documento {document_type} já foi enviado e está em análise"
                else:
                    return f"📋 Documento {document_type} ainda não foi enviado"
                    
            except Exception as e:
                logger.error(f"Error checking document status: {e}")
                return f"❌ Erro ao verificar status do documento: {str(e)}"
        
        return check_document_status
    
    def _create_list_required_documents_tool(self, tool_config: Dict[str, Any]) -> Callable:
        """Create list_required_documents tool from configuration"""
        
        async def list_required_documents(
            state: Dict[str, Any] = None
        ) -> str:
            """List required documents for check-in process
            
            Args:
                state: Current conversation state
                
            Returns:
                List of required documents
            """
            logger.info("Mike: Listing required documents")
            
            try:
                tenant_id = state.get("tenant_id") if state else self.tenant_id
                
                # Get required documents configuration
                required_docs = await db_service.get_required_documents_config(tenant_id)
                
                if not required_docs:
                    return "❌ Configuração de documentos não encontrada"
                
                # Format response
                response = "📋 Documentos necessários para check-in:\n\n"
                
                for doc in required_docs:
                    status_icon = "✅" if doc["is_required"] else "📄"
                    response += f"{status_icon} **{doc['type']}**: {doc['description']}\n"
                    
                    if doc.get("examples"):
                        examples = ", ".join(doc["examples"])
                        response += f"   Exemplos: {examples}\n"
                    
                    response += "\n"
                
                response += "⚠️ Todos os documentos devem estar legíveis e válidos."
                
                return response
                
            except Exception as e:
                logger.error(f"Error listing required documents: {e}")
                return f"❌ Erro ao listar documentos necessários: {str(e)}"
        
        return list_required_documents
    
    async def _simulate_name_extraction(self, document_type: str, base64_data: str) -> Optional[str]:
        """Simulate name extraction from document (replace with real OCR/AI service)"""
        # This is a simulation - in real implementation, use OCR/AI service
        # For now, return a placeholder name based on document type
        name_mapping = {
            "RG": "João Silva Santos",
            "CPF": "Maria Oliveira Costa", 
            "CNH": "Pedro Almeida Lima",
            "Passport": "Ana Rodrigues Ferreira"
        }
        
        # Simulate processing time
        import asyncio
        await asyncio.sleep(0.1)
        
        return name_mapping.get(document_type, "Nome Extraído")
    
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
        
        # Include new document tools in default tools
        return [
            validate_documents, 
            process_checkin, 
            get_required_documents,
            self._create_store_document_tool({}),
            self._create_extract_name_tool({}),
            self._create_check_document_status_tool({}),
            self._create_list_required_documents_tool({})
        ]
    
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
- **store_document**: Use para armazenar documentos recebidos (RG, CPF, CNH, Passport)
- **extract_name_from_document**: Use para extrair nome automaticamente do documento
- **check_document_status**: Use para verificar se documento já foi enviado
- **list_required_documents**: Use apenas quando solicitado pelo Supervisor

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
            "tools_count": len(self.tools_config) if self.tools_config else 7,
            "tools": [tool.get("name") for tool in self.tools_config] if self.tools_config else ["validate_documents", "process_checkin", "get_required_documents", "store_document", "extract_name_from_document", "check_document_status", "list_required_documents"],
            "prompt_length": len(self.prompt),
            "is_enabled": self.agent_config.get("is_enabled", True)
        }
