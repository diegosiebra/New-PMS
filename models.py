from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class ReservationData(BaseModel):
    """Reservation information for the current conversation"""
    reservation_id: Optional[str] = None
    checkin_date: Optional[str] = None
    checkin_time: Optional[str] = None
    checkout_date: Optional[str] = None
    checkout_time: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    step_status: Optional[str] = None
    listing_id: Optional[str] = None
    client_id: Optional[str] = None
    status: Optional[str] = None
    status_step_id: Optional[int] = None
    number_of_documents: Optional[int] = None
    docs_imediato: Optional[bool] = None
    in_manual: Optional[bool] = None
    guestsdetails: Optional[Dict[str, Any]] = None
    payload: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    # Customer information
    customer_name: Optional[str] = None
    customer_whatsapp: Optional[str] = None
    customer_external_id: Optional[str] = None
    customer_birthday: Optional[str] = None
    customer_fathers_name: Optional[str] = None
    customer_mothers_name: Optional[str] = None
    customer_cpf_rg_passaporte: Optional[str] = None
    customer_was_validated: Optional[bool] = None

class ConversationMessage(BaseModel):
    """Individual conversation message"""
    message_id: Optional[str] = None
    content: str
    from_me: bool  # True if from bot, False if from user
    timestamp: datetime
    agent_name: Optional[str] = None
    message_type: Optional[str] = None  # user_message, bot_response, system

class EnhancedAgentState(BaseModel):
    """Enhanced state with reservation data and conversation history"""
    messages: List[Dict[str, Any]]  # LangGraph messages
    tenant_id: str
    whatsapp_number: str
    conversation_id: str
    reservations: List[ReservationData] = []  # List of reservations for this WhatsApp number
    conversation_history: List[ConversationMessage] = []  # Last 20 messages
    current_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AgentState(BaseModel):
    messages: List[Dict[str, Any]]
    tenant_id: str
    conversation_id: str
    whatsapp_number: str
    current_agent: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AgentConfig(BaseModel):
    id: str
    tenant_id: str
    agent_type: str
    agent_name: str
    is_enabled: bool
    configuration: Optional[Dict[str, Any]] = None
    prompt: Optional[str] = None
    tools: Optional[List[Any]] = None
    model: str

class EvolutionWebhookPayload(BaseModel):
    event: str
    instance: str
    data: Dict[str, Any]

class AgentHandoff(BaseModel):
    from_agent: str
    to_agent: str
    reason: str
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.now()

class AgentResponse(BaseModel):
    success: bool = True
    message: str
    next_agent: Optional[str] = None
    handoff: Optional[AgentHandoff] = None
    update: Optional[AgentState] = None
    metadata: Optional[Dict[str, Any]] = None

class TenantContext(BaseModel):
    id: str
    name: str
    settings: Optional[Dict[str, Any]] = None
    evolution_api_config: Optional[Dict[str, str]] = None

class FragmentedMessage(BaseModel):
    """Represents a fragmented message being assembled"""
    message_id: str
    tenant_id: str
    whatsapp_number: str
    conversation_id: str
    fragments: List[str] = []
    total_fragments: Optional[int] = None
    current_fragment: int = 0
    timestamp: datetime
    timeout_seconds: int = 30  # Timeout para mensagens incompletas
    is_complete: bool = False
    assembled_content: Optional[str] = None

class MessageFragment(BaseModel):
    """Individual message fragment"""
    fragment_number: int
    content: str
    is_last: bool = False
    timestamp: datetime

class IDDocument(BaseModel):
    """Document information based on iddocuments table structure"""
    id: Optional[int] = None
    tenant_id: Optional[str] = None
    reservation_id: Optional[str] = None  # Links to Reservations.reservationid
    guest_id: Optional[int] = None
    type: str  # Document type (RG, CPF, CNH, Passport, etc.)
    document_number: Optional[str] = None
    person_name: Optional[str] = None
    birth_date: Optional[str] = None  # Date as string
    issuing_authority: Optional[str] = None
    validity_date: Optional[str] = None  # Date as string
    storage_path: str  # Path in Supabase Storage
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    status: str = "pending"  # pending, approved, rejected
    validation_status: str = "pending"  # pending, validated, invalid
    hash: Optional[str] = None
    base64_data: Optional[str] = None
    processing_metadata: Optional[Dict[str, Any]] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class DocumentValidation(BaseModel):
    """Document validation result"""
    document_id: int
    is_valid: bool
    validation_type: str  # legibility, completeness, authenticity
    confidence_score: Optional[float] = None
    issues: List[str] = []
    recommendations: List[str] = []

class RequiredDocument(BaseModel):
    """Required document for check-in process"""
    document_type: str
    is_required: bool = True
    description: str
    examples: Optional[List[str]] = None
    validation_rules: Optional[Dict[str, Any]] = None