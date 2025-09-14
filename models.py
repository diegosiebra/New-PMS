from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

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
