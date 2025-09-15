import logging
from typing import Dict, Any
from database import db_service
from agents import agent_manager
from message_buffer_service import message_buffer_service
from evolution_api_service import evolution_api_service

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
            message_id = key_data.get("id", "")
            
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
            
            # Process fragmented message through buffer service
            logger.info("Processing message through buffer service...")
            complete_message = await message_buffer_service.process_message(
                tenant_id=tenant_id,
                whatsapp_number=whatsapp_number,
                conversation_id=message_id,
                message_content=message_content,
                message_id=message_id
            )
            
            # If message is still being buffered (fragmented), don't process yet
            if complete_message is None:
                logger.info(f"Message buffered as fragment for tenant {tenant_id}, waiting for completion...")
                return
            
            logger.info(f"Complete message ready for processing: {complete_message}")
            
            # Process complete message with agent manager
            logger.info("Processing complete message with agent manager...")
            response = await self.agent_manager.process_message(
                tenant_id=tenant_id,
                message=complete_message,
                whatsapp_number=whatsapp_number,
                conversation_id=message_id
            )
            
            logger.info(f"Agent response: {response}")
            
            # Send response back via EvolutionAPI
            if response.get("success"):
                await self.send_response(tenant_id, whatsapp_number, response["message"])
            
            # Log the conversation
            await self.log_conversation(tenant_id, whatsapp_number, complete_message, response.get("message", ""), from_me)
            
        except Exception as e:
            logger.error(f"Error handling message for tenant {tenant_id}: {e}")
    
    async def send_response(self, tenant_id: str, whatsapp_number: str, message: str) -> None:
        """Send response via EvolutionAPI"""
        try:
            result = await evolution_api_service.send_text_message(tenant_id, whatsapp_number, message)
            
            if result.get("success"):
                logger.info(f"Message sent successfully to {whatsapp_number} for tenant {tenant_id}")
            else:
                logger.error(f"Error sending message: {result.get('error')}")
                    
        except Exception as e:
            logger.error(f"Error sending response for tenant {tenant_id}: {e}")
    
    async def log_conversation(self, tenant_id: str, whatsapp_number: str, user_message: str, bot_response: str, from_me: bool) -> None:
        """Log conversation to database"""
        try:
            # Note: Conversation logging is now handled by the agent manager
            # The agent manager already logs both user messages and bot responses
            # This method is kept for compatibility but no longer performs duplicate logging
            
            logger.info(f"Conversation processed for tenant {tenant_id}, number {whatsapp_number}")
            
        except Exception as e:
            logger.error(f"Error in conversation logging for tenant {tenant_id}: {e}")
    
    async def get_message_buffer_status(self) -> Dict[str, Any]:
        """Get status of message buffers for monitoring"""
        try:
            active_buffers = message_buffer_service.get_active_buffers_count()
            buffer_info = message_buffer_service.get_active_buffers_info()
            
            return {
                "active_buffers_count": active_buffers,
                "buffer_details": buffer_info,
                "status": "healthy" if active_buffers < 100 else "warning"  # Alert if too many buffers
            }
        except Exception as e:
            logger.error(f"Error getting buffer status: {e}")
            return {"error": str(e)}
    
    async def force_complete_fragmented_message(self, tenant_id: str, whatsapp_number: str, conversation_id: str) -> Dict[str, Any]:
        """Force complete a fragmented message (useful for debugging or manual intervention)"""
        try:
            complete_message = await message_buffer_service.force_complete_message(
                tenant_id, whatsapp_number, conversation_id
            )
            
            if complete_message:
                return {
                    "success": True,
                    "message": "Message completed successfully",
                    "complete_message": complete_message
                }
            else:
                return {
                    "success": False,
                    "message": "No active buffer found for this conversation"
                }
        except Exception as e:
            logger.error(f"Error forcing message completion: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_media_message(self, tenant_id: str, whatsapp_number: str, media_url: str, 
                               media_type: str = "image", caption: str = "") -> Dict[str, Any]:
        """Send media message via EvolutionAPI"""
        try:
            result = await evolution_api_service.send_media_message(
                tenant_id, whatsapp_number, media_url, media_type, caption
            )
            return result
        except Exception as e:
            logger.error(f"Error sending media message for tenant {tenant_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def send_template_message(self, tenant_id: str, whatsapp_number: str, template_name: str, 
                                  parameters: list = None) -> Dict[str, Any]:
        """Send template message via EvolutionAPI"""
        try:
            result = await evolution_api_service.send_template_message(
                tenant_id, whatsapp_number, template_name, parameters
            )
            return result
        except Exception as e:
            logger.error(f"Error sending template message for tenant {tenant_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_instance_status(self, tenant_id: str) -> Dict[str, Any]:
        """Get Evolution API instance status"""
        try:
            result = await evolution_api_service.get_instance_status(tenant_id)
            return result
        except Exception as e:
            logger.error(f"Error getting instance status for tenant {tenant_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def mark_message_as_read(self, tenant_id: str, whatsapp_number: str, message_id: str) -> Dict[str, Any]:
        """Mark message as read via EvolutionAPI"""
        try:
            result = await evolution_api_service.mark_message_as_read(tenant_id, whatsapp_number, message_id)
            return result
        except Exception as e:
            logger.error(f"Error marking message as read for tenant {tenant_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_profile_picture(self, tenant_id: str, whatsapp_number: str) -> Dict[str, Any]:
        """Get profile picture via EvolutionAPI"""
        try:
            result = await evolution_api_service.get_profile_picture(tenant_id, whatsapp_number)
            return result
        except Exception as e:
            logger.error(f"Error getting profile picture for tenant {tenant_id}: {e}")
            return {"success": False, "error": str(e)}

# Global webhook service instance
webhook_service = WebhookService()
