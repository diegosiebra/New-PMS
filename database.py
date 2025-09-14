import os
from supabase import create_client, Client
from typing import List, Dict, Any, Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
        
        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
    
    async def get_tenant(self, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Get tenant information from database"""
        try:
            response = self.supabase.table("tenantnew").select("*").eq("id", tenant_id).execute()
            if response.data:
                return response.data[0]
            return None
        except Exception as e:
            logger.error(f"Error getting tenant {tenant_id}: {e}")
            return None
    
    async def get_agent_configurations(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get agent configurations for a tenant"""
        try:
            response = self.supabase.table("agent_configurations").select("*").eq("tenant_id", tenant_id).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting agent configurations for tenant {tenant_id}: {e}")
            return []
    
    async def log_agent_execution(self, execution: Dict[str, Any]) -> bool:
        """Log agent execution to database"""
        try:
            response = self.supabase.table("agent_executions").insert({
                "tenant_id": execution["tenant_id"],
                "conversation_id": execution["conversation_id"],
                "agent_type": execution["agent_type"],
                "agent_name": execution["agent_name"],
                "input": execution.get("input"),
                "output": execution.get("output"),
                "status": execution["status"],
                "execution_time": execution.get("execution_time"),
                "error_message": execution.get("error_message"),
                "created_at": execution.get("created_at")
            }).execute()
            return True
        except Exception as e:
            logger.error(f"Error logging agent execution: {e}")
            return False
    
    async def get_conversation_history(self, tenant_id: str, whatsapp_number: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get conversation history for a WhatsApp number"""
        try:
            # Get conversation history from agent_executions table
            response = self.supabase.table("agent_executions").select("*").eq("tenant_id", tenant_id).eq("conversation_id", whatsapp_number).order("created_at", desc=True).limit(limit).execute()
            return response.data or []
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    async def save_conversation_message(self, tenant_id: str, whatsapp_number: str, message: str, from_me: bool) -> bool:
        """Save a conversation message to database"""
        try:
            # Log conversation as agent execution instead of using n8n_chat_histories
            agent_name = "User" if not from_me else "Bot"
            agent_type = "user_message" if not from_me else "bot_response"
            
            await self.log_agent_execution({
                "tenant_id": tenant_id,
                "conversation_id": whatsapp_number,
                "agent_type": agent_type,
                "agent_name": agent_name,
                "input": {"message": message},
                "output": None,
                "status": "success",
                "execution_time": None,
                "error_message": None,
                "created_at": "now()"
            })
            return True
        except Exception as e:
            logger.error(f"Error saving conversation message: {e}")
            return False

# Global database service instance
db_service = DatabaseService()
