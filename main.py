import os
import logging
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from webhook_service import webhook_service
from agents import agent_manager
from database import db_service
from models import EvolutionWebhookPayload

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LangGraph Agent Service",
    description="Multi-agent LangGraph service for EvolutionAPI webhook integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("🚀 Starting LangGraph Agent Service")
    
    # Validate required environment variables
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_SERVICE_KEY", 
        "DATABASE_URL",
        "OPENAI_API_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        raise ValueError(f"Missing required environment variables: {missing_vars}")
    
    logger.info("✅ Environment variables validated")
    logger.info("🎯 Service ready to process webhooks")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "LangGraph Agent Service",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "success": True,
        "message": "Agent service is running",
        "status": "healthy"
    }

@app.post("/api/webhooks/evolution/{tenant_id}")
async def evolution_webhook_with_tenant_id(tenant_id: str, payload: EvolutionWebhookPayload):
    """EvolutionAPI webhook endpoint with tenant ID in URL"""
    try:
        result = await webhook_service.process_evolution_webhook(tenant_id, payload.dict())
        return result
    except Exception as e:
        logger.error(f"Error processing webhook for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/webhook/evolution")
async def evolution_webhook_singular(
    payload: EvolutionWebhookPayload,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
):
    """EvolutionAPI webhook endpoint (singular, without tenant ID in URL)"""
    try:
        # Extract instance from payload
        instance_name = payload.instance
        if not instance_name:
            raise HTTPException(
                status_code=400, 
                detail="Instance name is required in payload"
            )
        
        # Look up tenant_id by instance name
        tenant_data = await db_service.get_tenant_by_instance(instance_name)
        if not tenant_data:
            raise HTTPException(
                status_code=404, 
                detail=f"No tenant found for instance: {instance_name}"
            )
        
        tenant_id = tenant_data['id']
        logger.info(f"Resolved tenant_id {tenant_id} for instance {instance_name}")
        
        # Process webhook with resolved tenant_id
        result = await webhook_service.process_evolution_webhook(tenant_id, payload.dict())
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing webhook for instance {payload.instance}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/agents/{tenant_id}")
async def get_agents(tenant_id: str):
    """Get all agents for a tenant"""
    try:
        # Initialize agents if not already done
        await agent_manager.initialize_tenant_agents(tenant_id)
        
        agent_configs = await db_service.get_agent_configurations(tenant_id)
        
        agent_list = []
        for config in agent_configs:
            agent_list.append({
                "name": config.get("agent_name", ""),
                "type": config.get("agent_type", ""),
                "enabled": config.get("is_enabled", False),
                "description": config.get("prompt", "")[:100] + "..." if config.get("prompt") else ""
            })
        
        return {
            "success": True,
            "data": {
                "tenant_id": tenant_id,
                "agents": agent_list,
                "total_agents": len(agent_list)
            }
        }
    except Exception as e:
        logger.error(f"Error getting agents for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/agents/{tenant_id}/stats")
async def get_agent_stats(tenant_id: str):
    """Get agent statistics for a tenant"""
    try:
        # Initialize agents if not already done
        await agent_manager.initialize_tenant_agents(tenant_id)
        
        agent_configs = await db_service.get_agent_configurations(tenant_id)
        
        stats = {
            "total_agents": len(agent_configs),
            "active_agents": len([config for config in agent_configs if config.get("is_enabled", False)]),
            "agents": [
                {
                    "name": config.get("agent_name", ""),
                    "type": config.get("agent_type", ""),
                    "enabled": config.get("is_enabled", False),
                    "description": config.get("prompt", "")[:100] + "..." if config.get("prompt") else ""
                }
                for config in agent_configs
            ],
            "supervisor_available": tenant_id in agent_manager.supervisors,
            "agents_initialized": tenant_id in agent_manager.agents
        }
        
        return {
            "success": True,
            "data": {
                "tenant_id": tenant_id,
                "stats": stats
            }
        }
    except Exception as e:
        logger.error(f"Error getting agent stats for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/agents/{tenant_id}/reload")
async def reload_agents(tenant_id: str):
    """Reload agents for a tenant"""
    try:
        # Clear existing agents
        if tenant_id in agent_manager.agents:
            del agent_manager.agents[tenant_id]
        if tenant_id in agent_manager.supervisors:
            del agent_manager.supervisors[tenant_id]
        
        # Reinitialize
        success = await agent_manager.initialize_tenant_agents(tenant_id)
        
        if success:
            return {
                "success": True,
                "message": f"Agents reloaded successfully for tenant {tenant_id}"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to reload agents")
            
    except Exception as e:
        logger.error(f"Error reloading agents for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/configurations/{tenant_id}")
async def get_configurations(tenant_id: str):
    """Get agent configurations for a tenant"""
    try:
        configurations = await db_service.get_agent_configurations(tenant_id)
        
        config_list = []
        for config in configurations:
            config_list.append({
                "id": config.get("id"),
                "agent_type": config.get("agent_type"),
                "agent_name": config.get("agent_name"),
                "is_enabled": config.get("is_enabled"),
                "configuration": config.get("configuration"),
                "prompt": config.get("prompt"),
                "model": config.get("model"),
                "created_at": config.get("created_at"),
                "updated_at": config.get("updated_at")
            })
        
        return {
            "success": True,
            "data": {
                "tenant_id": tenant_id,
                "configurations": config_list
            }
        }
    except Exception as e:
        logger.error(f"Error getting configurations for tenant {tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/message-buffers/status")
async def get_message_buffer_status():
    """Get status of message buffers for monitoring fragmented messages"""
    try:
        status = await webhook_service.get_message_buffer_status()
        return {
            "success": True,
            "data": status
        }
    except Exception as e:
        logger.error(f"Error getting message buffer status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/message-buffers/{tenant_id}/force-complete")
async def force_complete_fragmented_message(
    tenant_id: str,
    whatsapp_number: str,
    conversation_id: str
):
    """Force complete a fragmented message (useful for debugging or manual intervention)"""
    try:
        result = await webhook_service.force_complete_fragmented_message(
            tenant_id, whatsapp_number, conversation_id
        )
        return result
    except Exception as e:
        logger.error(f"Error forcing message completion: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/message-buffers/{tenant_id}/check-completed")
async def check_completed_buffers(
    tenant_id: str,
    whatsapp_number: str
):
    """Check and process any completed sequence buffers"""
    try:
        result = await webhook_service.check_and_process_completed_buffers(
            tenant_id, whatsapp_number
        )
        if result:
            return {
                "success": True,
                "message": "Completed buffer processed",
                "complete_message": result
            }
        else:
            return {
                "success": False,
                "message": "No completed buffers found"
            }
    except Exception as e:
        logger.error(f"Error checking completed buffers: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/evolution/{tenant_id}/send-media")
async def send_media_message(
    tenant_id: str,
    whatsapp_number: str,
    media_url: str,
    media_type: str = "image",
    caption: str = ""
):
    """Send media message via Evolution API"""
    try:
        result = await webhook_service.send_media_message(
            tenant_id, whatsapp_number, media_url, media_type, caption
        )
        return result
    except Exception as e:
        logger.error(f"Error sending media message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/evolution/{tenant_id}/send-template")
async def send_template_message(
    tenant_id: str,
    whatsapp_number: str,
    template_name: str,
    parameters: list = None
):
    """Send template message via Evolution API"""
    try:
        result = await webhook_service.send_template_message(
            tenant_id, whatsapp_number, template_name, parameters
        )
        return result
    except Exception as e:
        logger.error(f"Error sending template message: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/evolution/{tenant_id}/instance-status")
async def get_instance_status(tenant_id: str):
    """Get Evolution API instance status"""
    try:
        result = await webhook_service.get_instance_status(tenant_id)
        return result
    except Exception as e:
        logger.error(f"Error getting instance status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/api/evolution/{tenant_id}/mark-read")
async def mark_message_as_read(
    tenant_id: str,
    whatsapp_number: str,
    message_id: str
):
    """Mark message as read via Evolution API"""
    try:
        result = await webhook_service.mark_message_as_read(
            tenant_id, whatsapp_number, message_id
        )
        return result
    except Exception as e:
        logger.error(f"Error marking message as read: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/evolution/{tenant_id}/profile-picture")
async def get_profile_picture(tenant_id: str, whatsapp_number: str):
    """Get profile picture via Evolution API"""
    try:
        result = await webhook_service.get_profile_picture(tenant_id, whatsapp_number)
        return result
    except Exception as e:
        logger.error(f"Error getting profile picture: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 3001))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"🚀 Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
