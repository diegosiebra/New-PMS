"""
State Management for LangGraph Multi-Agent System
Handles enhanced state with reservation data and conversation history
"""

from typing import List, Dict, Any, Optional, Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from datetime import datetime
import logging
from database import db_service
from models import ReservationData, ConversationMessage

logger = logging.getLogger(__name__)

class SupervisorState(TypedDict, total=False):
    """Enhanced state for the supervisor and agents"""
    messages: Annotated[list, add_messages]  # LangGraph messages for conversation flow
    tenant_id: str
    whatsapp_number: str
    conversation_id: str
    reservations: List[Dict[str, Any]]  # JSON list of reservations
    conversation_history: List[Dict[str, Any]]  # Last 20 messages
    current_agent: Optional[str]
    metadata: Optional[Dict[str, Any]]
    remaining_steps: Optional[int]  # Required for langgraph_supervisor

class StateManager:
    """Manages state data loading and formatting for agents"""
    
    @staticmethod
    async def load_state_data(tenant_id: str, whatsapp_number: str, conversation_id: str = None) -> Dict[str, Any]:
        """Load all state data for a conversation"""
        try:
            # Use whatsapp_number as conversation_id if not provided
            if not conversation_id:
                conversation_id = whatsapp_number
            
            # Load reservations
            reservations_data = await db_service.get_reservations_by_whatsapp(tenant_id, whatsapp_number)
            reservations = []
            
            for res_data in reservations_data:
                # Extract customer information
                customer_data = res_data.get("Customers", {})
                
                reservation = {
                    "reservation_id": res_data.get("reservationid"),
                    "checkin_date": res_data.get("checkindate"),
                    "checkin_time": res_data.get("checkintime"),
                    "checkout_date": res_data.get("checkoutdate"),
                    "checkout_time": res_data.get("checkouttime"),
                    "tags": res_data.get("tags", {}),
                    "step_status": res_data.get("status"),
                    "listing_id": res_data.get("listingid"),
                    "client_id": res_data.get("clientid"),
                    "status": res_data.get("status"),
                    "status_step_id": res_data.get("status_step_id"),
                    "number_of_documents": res_data.get("number_of_documents"),
                    "docs_imediato": res_data.get("docs_imediato"),
                    "in_manual": res_data.get("in_manual"),
                    "guestsdetails": res_data.get("guestsdetails"),
                    "payload": res_data.get("payload"),
                    "created_at": res_data.get("created_at"),
                    # Customer information
                    "customer_name": customer_data.get("customername"),
                    "customer_whatsapp": customer_data.get("customerwhatsapp"),
                    "customer_external_id": customer_data.get("externalid"),
                    "customer_birthday": customer_data.get("birthday"),
                    "customer_fathers_name": customer_data.get("fathersname"),
                    "customer_mothers_name": customer_data.get("mothersname"),
                    "customer_cpf_rg_passaporte": customer_data.get("cpf_rg_passaporte"),
                    "customer_was_validated": customer_data.get("wasvalidated")
                }
                reservations.append(reservation)
            
            # Load conversation history
            history_data = await db_service.get_conversation_history(tenant_id, whatsapp_number, limit=20)
            conversation_history = []
            
            for msg_data in history_data:
                message = {
                    "message_id": msg_data.get("id"),
                    "content": StateManager._extract_message_content(msg_data),
                    "from_me": msg_data.get("agent_type") == "bot_response",
                    "timestamp": msg_data.get("created_at"),
                    "agent_name": msg_data.get("agent_name"),
                    "message_type": msg_data.get("agent_type")
                }
                conversation_history.append(message)
            
            # Reverse to get chronological order (oldest first)
            conversation_history.reverse()
            
            logger.info(f"Loaded state data for {whatsapp_number}: {len(reservations)} reservations, {len(conversation_history)} messages")
            
            return {
                "tenant_id": tenant_id,
                "whatsapp_number": whatsapp_number,
                "conversation_id": conversation_id,
                "reservations": reservations,
                "conversation_history": conversation_history,
                "current_agent": None,
                "metadata": {
                    "loaded_at": datetime.now().isoformat(),
                    "reservations_count": len(reservations),
                    "history_count": len(conversation_history)
                }
            }
            
        except Exception as e:
            logger.error(f"Error loading state data for {whatsapp_number}: {e}")
            return {
                "tenant_id": tenant_id,
                "whatsapp_number": whatsapp_number,
                "conversation_id": conversation_id or whatsapp_number,
                "reservations": [],
                "conversation_history": [],
                "current_agent": None,
                "metadata": {"error": str(e)}
            }
    
    @staticmethod
    def _extract_message_content(msg_data: Dict[str, Any]) -> str:
        """Extract message content from agent execution data"""
        try:
            # For user messages, get from input
            if msg_data.get("agent_type") == "user_message":
                if msg_data.get("input") and isinstance(msg_data["input"], dict):
                    return msg_data["input"].get("message", "")
            
            # For bot responses, get from output
            elif msg_data.get("agent_type") in ["bot_response", "supervisor"]:
                if msg_data.get("output") and isinstance(msg_data["output"], dict):
                    return msg_data["output"].get("response", "") or msg_data["output"].get("message", "")
            
            # Fallback: try both input and output
            if msg_data.get("input") and isinstance(msg_data["input"], dict):
                if "message" in msg_data["input"]:
                    return msg_data["input"]["message"]
            
            if msg_data.get("output") and isinstance(msg_data["output"], dict):
                if "response" in msg_data["output"]:
                    return msg_data["output"]["response"]
                elif "message" in msg_data["output"]:
                    return msg_data["output"]["message"]
            
            # Last fallback
            return msg_data.get("agent_name", "")
            
        except Exception as e:
            logger.warning(f"Error extracting message content: {e}")
            return ""
    
    @staticmethod
    def create_initial_state(tenant_id: str, whatsapp_number: str, message: str, state_data: Dict[str, Any]) -> SupervisorState:
        """Create initial state for LangGraph with loaded data"""
        from langchain_core.messages import HumanMessage
        
        return SupervisorState(
            messages=[HumanMessage(content=message)],
            tenant_id=tenant_id,
            whatsapp_number=whatsapp_number,
            conversation_id=state_data.get("conversation_id", whatsapp_number),
            reservations=state_data.get("reservations", []),
            conversation_history=state_data.get("conversation_history", []),
            current_agent=None,
            metadata=state_data.get("metadata", {}),
            remaining_steps=3  # Limit steps to prevent recursion loops
        )
    
    @staticmethod
    def format_state_for_agents(state: SupervisorState) -> str:
        """Format state information for agents to use in their prompts"""
        try:
            state_info = []
            
            # Add basic context
            state_info.append(f"🏠 **Contexto da Conversa:**")
            state_info.append(f"- Tenant: {state['tenant_id']}")
            state_info.append(f"- WhatsApp: {state['whatsapp_number']}")
            
            # Add reservation information
            if state.get("reservations"):
                state_info.append(f"\n📋 **Reservas ({len(state['reservations'])}):**")
                for i, reservation in enumerate(state["reservations"][:3]):  # Show max 3 reservations
                    res_info = []
                    if reservation.get("reservation_id"):
                        res_info.append(f"ID: {reservation['reservation_id']}")
                    if reservation.get("customer_name"):
                        res_info.append(f"Cliente: {reservation['customer_name']}")
                    if reservation.get("checkin_date"):
                        res_info.append(f"Check-in: {reservation['checkin_date']} {reservation.get('checkin_time', '')}")
                    if reservation.get("checkout_date"):
                        res_info.append(f"Check-out: {reservation['checkout_date']} {reservation.get('checkout_time', '')}")
                    if reservation.get("status"):
                        res_info.append(f"Status: {reservation['status']}")
                    if reservation.get("listing_id"):
                        res_info.append(f"Propriedade: {reservation['listing_id']}")
                    if reservation.get("number_of_documents"):
                        res_info.append(f"Docs: {reservation['number_of_documents']}")
                    
                    if res_info:
                        state_info.append(f"  {i+1}. {' | '.join(res_info)}")
            else:
                state_info.append(f"\n📋 **Reservas:** Nenhuma reserva encontrada")
            
            # Add recent conversation context
            if state.get("conversation_history"):
                recent_messages = state["conversation_history"][-10:]  # Last 10 messages for better context
                state_info.append(f"\n💬 **Contexto da Conversa (últimas {len(recent_messages)} mensagens):**")
                for msg in recent_messages:
                    sender = "🤖 Bot" if msg.get("from_me") else "👤 Cliente"
                    content = msg.get("content", "")[:150]  # Increase truncation limit
                    if len(msg.get("content", "")) > 150:
                        content += "..."
                    state_info.append(f"  {sender}: {content}")
            
            # Add metadata
            if state.get("metadata"):
                metadata = state["metadata"]
                if metadata.get("reservations_count") is not None:
                    state_info.append(f"\n📊 **Estatísticas:**")
                    state_info.append(f"- Total de reservas: {metadata['reservations_count']}")
                    state_info.append(f"- Mensagens no histórico: {metadata['history_count']}")
            
            return "\n".join(state_info)
            
        except Exception as e:
            logger.error(f"Error formatting state for agents: {e}")
            return f"⚠️ Erro ao carregar contexto: {str(e)}"

# Global state manager instance
state_manager = StateManager()
