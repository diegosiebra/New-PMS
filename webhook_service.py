import httpx
import logging
from typing import Dict, Any
from database import db_service
from agents import agent_manager
import os

logger = logging.getLogger(__name__)

class WebhookService:
    def __init__(self):
        self.agent_manager = agent_manager
    
    async def process_evolution_webhook(self, tenant_id: str, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process EvolutionAPI webhook"""
        try:
            event = webhook_data.get("event")
            instance = webhook_data.get("instance")
            data = webhook_data.get("data", {})
            
            logger.info(f"EvolutionAPI Webhook received for tenant {tenant_id}: {event}")
            
            # Verify tenant exists
            tenant = await db_service.get_tenant(tenant_id)
            if not tenant:
                logger.error(f"Tenant {tenant_id} not found")
                return {"success": False, "message": "Tenant não encontrado"}
            
            # Process different event types
            if event == "CONNECTION_UPDATE":
                await self.handle_connection_update(tenant_id, data)
            elif event == "MESSAGES_UPSERT":
                await self.handle_message_received(tenant_id, data)
            else:
                logger.info(f"Unhandled EvolutionAPI event: {event}")
            
            return {"success": True}
            
        except Exception as e:
            logger.error(f"EvolutionAPI webhook error: {e}")
            return {"success": False, "message": "Erro ao processar webhook"}
    
    async def handle_connection_update(self, tenant_id: str, data: Dict[str, Any]) -> None:
        """Handle connection update"""
        try:
            logger.info(f"Connection update for tenant {tenant_id}: {data}")
            
            # Get current tenant data to preserve existing settings
            tenant = await db_service.get_tenant(tenant_id)
            if not tenant:
                logger.error(f"Tenant {tenant_id} not found")
                return
            
            # Update connection status (this would need to be implemented in database service)
            # For now, just log the update
            logger.info(f"Updated connection status for tenant {tenant_id}: {data.get('state', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Error handling connection update for tenant {tenant_id}: {e}")
    
    async def handle_message_received(self, tenant_id: str, data: Dict[str, Any]) -> None:
        """Handle message received"""
        try:
            logger.info(f"Message received for tenant {tenant_id}")
            
            # Extract message information
            message_data = data.get("message", {})
            key_data = data.get("key", {})
            remote_jid = key_data.get("remoteJid", "")
            from_me = key_data.get("fromMe", False)
            
            # Skip messages from the bot itself
            if from_me:
                logger.info(f"Skipping message from bot for tenant {tenant_id}")
                return
            
            # Extract message content
            message_content = ""
            if "conversation" in message_data:
                message_content = message_data["conversation"]
            elif "extendedTextMessage" in message_data:
                message_content = message_data["extendedTextMessage"].get("text", "")
            
            logger.info(f"Message content: {message_content}")
            
            if not message_content.strip():
                logger.info(f"Skipping empty message for tenant {tenant_id}")
                return
            
            # Extract WhatsApp number from remoteJid
            whatsapp_number = remote_jid.replace("@s.whatsapp.net", "").replace("@c.us", "")
            logger.info(f"WhatsApp number: {whatsapp_number}")
            
            # Process message with agent manager
            logger.info("Processing message with agent manager...")
            response = await self.agent_manager.process_message(
                tenant_id=tenant_id,
                message=message_content,
                whatsapp_number=whatsapp_number,
                conversation_id=key_data.get("id")
            )
            
            logger.info(f"Agent response: {response}")
            
            # Send response back via EvolutionAPI
            if response.get("success"):
                await self.send_response(tenant_id, whatsapp_number, response["message"])
            
            # Log the conversation
            await self.log_conversation(tenant_id, whatsapp_number, message_content, response.get("message", ""), from_me)
            
        except Exception as e:
            logger.error(f"Error handling message for tenant {tenant_id}: {e}")
    
    async def send_response(self, tenant_id: str, whatsapp_number: str, message: str) -> None:
        """Send response via EvolutionAPI"""
        try:
            # Get tenant EvolutionAPI configuration
            tenant = await db_service.get_tenant(tenant_id)
            evolution_config = tenant.get("settings", {}).get("evolution", {})
            
            base_url = evolution_config.get("baseUrl")
            api_key = evolution_config.get("apiKey")
            instance_name = evolution_config.get("instanceName")
            
            if not all([base_url, api_key, instance_name]):
                logger.error(f"Missing EvolutionAPI configuration for tenant {tenant_id}")
                return
            
            # Send message via EvolutionAPI
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/message/sendText/{instance_name}",
                    headers={
                        "Content-Type": "application/json",
                        "apikey": api_key,
                    },
                    json={
                        "number": whatsapp_number,
                        "text": message
                    }
                )
                
                if response.status_code == 200:
                    logger.info(f"Message sent successfully to {whatsapp_number} for tenant {tenant_id}")
                else:
                    logger.error(f"Error sending message via EvolutionAPI: {response.status_code} - {response.text}")
                    
        except Exception as e:
            logger.error(f"Error sending response for tenant {tenant_id}: {e}")
    
    async def log_conversation(self, tenant_id: str, whatsapp_number: str, user_message: str, bot_response: str, from_me: bool) -> None:
        """Log conversation to database"""
        try:
            # Log user message
            await db_service.save_conversation_message(tenant_id, whatsapp_number, user_message, False)
            
            # Log bot response
            await db_service.save_conversation_message(tenant_id, whatsapp_number, bot_response, True)
            
            logger.info(f"Conversation logged for tenant {tenant_id}, number {whatsapp_number}")
            
        except Exception as e:
            logger.error(f"Error logging conversation for tenant {tenant_id}: {e}")

# Global webhook service instance
webhook_service = WebhookService()
