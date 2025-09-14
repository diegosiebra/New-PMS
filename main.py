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
    if not x_tenant_id:
        raise HTTPException(
            status_code=400, 
            detail="Tenant ID is required in X-Tenant-ID header"
        )
    
    try:
        result = await webhook_service.process_evolution_webhook(x_tenant_id, payload.dict())
        return result
    except Exception as e:
        logger.error(f"Error processing webhook for tenant {x_tenant_id}: {e}")
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
