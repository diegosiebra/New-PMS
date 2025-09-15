import httpx
import logging
import os
from typing import Dict, Any, Optional, List
from database import db_service

logger = logging.getLogger(__name__)

class EvolutionAPIService:
    """Service to handle Evolution API communication"""
    
    def __init__(self):
        self.api_key = os.getenv("EVOLUTION_API_KEY")
        if not self.api_key:
            logger.warning("EVOLUTION_API_KEY not found in environment variables")
    
    async def get_tenant_evolution_config(self, tenant_id: str) -> Optional[Dict[str, str]]:
        """Get Evolution API configuration for a tenant"""
        try:
            tenant = await db_service.get_tenant(tenant_id)
            if not tenant:
                logger.error(f"Tenant {tenant_id} not found")
                return None
            
            evolution_config = tenant.get("settings", {}).get("evolution", {})
            
            base_url = evolution_config.get("baseUrl")
            instance_name = evolution_config.get("instanceName")
            
            if not all([base_url, instance_name, self.api_key]):
                logger.error(f"Missing EvolutionAPI configuration for tenant {tenant_id}")
                return None
            
            return {
                "base_url": base_url,
                "api_key": self.api_key,
                "instance_name": instance_name
            }
            
        except Exception as e:
            logger.error(f"Error getting Evolution config for tenant {tenant_id}: {e}")
            return None
    
    async def send_text_message(self, tenant_id: str, whatsapp_number: str, message: str) -> Dict[str, Any]:
        """Send text message via Evolution API"""
        try:
            config = await self.get_tenant_evolution_config(tenant_id)
            if not config:
                return {
                    "success": False,
                    "error": "Evolution API configuration not found"
                }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{config['base_url']}/message/sendText/{config['instance_name']}",
                    headers={
                        "Content-Type": "application/json",
                        "apikey": config["api_key"],
                    },
                    json={
                        "number": whatsapp_number,
                        "text": message
                    }
                )
                
                if response.status_code in [200, 201]:  # Accept both 200 and 201 as success
                    logger.info(f"Message sent successfully to {whatsapp_number} for tenant {tenant_id}")
                    return {
                        "success": True,
                        "message": "Message sent successfully",
                        "response": response.json() if response.content else {}
                    }
                else:
                    logger.error(f"Error sending message via EvolutionAPI: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Evolution API error: {response.status_code} - {response.text}"
                    }
                    
        except Exception as e:
            logger.error(f"Error sending message for tenant {tenant_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_media_message(self, tenant_id: str, whatsapp_number: str, media_url: str, 
                               media_type: str = "image", caption: str = "") -> Dict[str, Any]:
        """Send media message via Evolution API"""
        try:
            config = await self.get_tenant_evolution_config(tenant_id)
            if not config:
                return {
                    "success": False,
                    "error": "Evolution API configuration not found"
                }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{config['base_url']}/message/sendMedia/{config['instance_name']}",
                    headers={
                        "Content-Type": "application/json",
                        "apikey": config["api_key"],
                    },
                    json={
                        "number": whatsapp_number,
                        "mediaUrl": media_url,
                        "mediaType": media_type,
                        "caption": caption
                    }
                )
                
                if response.status_code in [200, 201]:  # Accept both 200 and 201 as success
                    logger.info(f"Media message sent successfully to {whatsapp_number} for tenant {tenant_id}")
                    return {
                        "success": True,
                        "message": "Media message sent successfully",
                        "response": response.json() if response.content else {}
                    }
                else:
                    logger.error(f"Error sending media message via EvolutionAPI: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Evolution API error: {response.status_code} - {response.text}"
                    }
                    
        except Exception as e:
            logger.error(f"Error sending media message for tenant {tenant_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_template_message(self, tenant_id: str, whatsapp_number: str, template_name: str, 
                                  parameters: List[str] = None) -> Dict[str, Any]:
        """Send template message via Evolution API"""
        try:
            config = await self.get_tenant_evolution_config(tenant_id)
            if not config:
                return {
                    "success": False,
                    "error": "Evolution API configuration not found"
                }
            
            payload = {
                "number": whatsapp_number,
                "templateName": template_name
            }
            
            if parameters:
                payload["parameters"] = parameters
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{config['base_url']}/message/sendTemplate/{config['instance_name']}",
                    headers={
                        "Content-Type": "application/json",
                        "apikey": config["api_key"],
                    },
                    json=payload
                )
                
                if response.status_code in [200, 201]:  # Accept both 200 and 201 as success
                    logger.info(f"Template message sent successfully to {whatsapp_number} for tenant {tenant_id}")
                    return {
                        "success": True,
                        "message": "Template message sent successfully",
                        "response": response.json() if response.content else {}
                    }
                else:
                    logger.error(f"Error sending template message via EvolutionAPI: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Evolution API error: {response.status_code} - {response.text}"
                    }
                    
        except Exception as e:
            logger.error(f"Error sending template message for tenant {tenant_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_instance_status(self, tenant_id: str) -> Dict[str, Any]:
        """Get Evolution API instance status"""
        try:
            config = await self.get_tenant_evolution_config(tenant_id)
            if not config:
                return {
                    "success": False,
                    "error": "Evolution API configuration not found"
                }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config['base_url']}/instance/connectionState/{config['instance_name']}",
                    headers={
                        "apikey": config["api_key"],
                    }
                )
                
                if response.status_code in [200, 201]:  # Accept both 200 and 201 as success
                    return {
                        "success": True,
                        "status": response.json() if response.content else {}
                    }
                else:
                    logger.error(f"Error getting instance status: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Evolution API error: {response.status_code} - {response.text}"
                    }
                    
        except Exception as e:
            logger.error(f"Error getting instance status for tenant {tenant_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def mark_message_as_read(self, tenant_id: str, whatsapp_number: str, message_id: str) -> Dict[str, Any]:
        """Mark message as read via Evolution API"""
        try:
            config = await self.get_tenant_evolution_config(tenant_id)
            if not config:
                return {
                    "success": False,
                    "error": "Evolution API configuration not found"
                }
            
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{config['base_url']}/chat/markMessageAsRead/{config['instance_name']}",
                    headers={
                        "Content-Type": "application/json",
                        "apikey": config["api_key"],
                    },
                    json={
                        "number": whatsapp_number,
                        "messageId": message_id
                    }
                )
                
                if response.status_code in [200, 201]:  # Accept both 200 and 201 as success
                    logger.info(f"Message marked as read for {whatsapp_number} for tenant {tenant_id}")
                    return {
                        "success": True,
                        "message": "Message marked as read"
                    }
                else:
                    logger.error(f"Error marking message as read: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Evolution API error: {response.status_code} - {response.text}"
                    }
                    
        except Exception as e:
            logger.error(f"Error marking message as read for tenant {tenant_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_profile_picture(self, tenant_id: str, whatsapp_number: str) -> Dict[str, Any]:
        """Get profile picture via Evolution API"""
        try:
            config = await self.get_tenant_evolution_config(tenant_id)
            if not config:
                return {
                    "success": False,
                    "error": "Evolution API configuration not found"
                }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{config['base_url']}/chat/getProfilePicture/{config['instance_name']}",
                    headers={
                        "apikey": config["api_key"],
                    },
                    params={
                        "number": whatsapp_number
                    }
                )
                
                if response.status_code in [200, 201]:  # Accept both 200 and 201 as success
                    return {
                        "success": True,
                        "profile_picture": response.json() if response.content else {}
                    }
                else:
                    logger.error(f"Error getting profile picture: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"Evolution API error: {response.status_code} - {response.text}"
                    }
                    
        except Exception as e:
            logger.error(f"Error getting profile picture for tenant {tenant_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Global Evolution API service instance
evolution_api_service = EvolutionAPIService()
