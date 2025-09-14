#!/usr/bin/env python3
"""
Test script for LangGraph Agent Service
"""

import asyncio
import os
from dotenv import load_dotenv
from agents import agent_manager
from database import db_service

async def test_agent_initialization():
    """Test agent initialization"""
    print("🧪 Testing Agent Initialization")
    print("=" * 40)
    
    tenant_id = "test-tenant-123"
    
    try:
        # Test agent initialization
        success = await agent_manager.initialize_tenant_agents(tenant_id)
        
        if success:
            print("✅ Agent initialization successful")
            print(f"📊 Agents created: {len(agent_manager.agents.get(tenant_id, []))}")
            print(f"🎯 Supervisor available: {tenant_id in agent_manager.supervisors}")
        else:
            print("❌ Agent initialization failed")
            
    except Exception as e:
        print(f"❌ Error during initialization: {e}")

async def test_message_processing():
    """Test message processing"""
    print("\n🧪 Testing Message Processing")
    print("=" * 40)
    
    tenant_id = "test-tenant-123"
    test_messages = [
        "Preciso de ajuda com documentos para check-in",
        "Quais são as regras da casa?",
        "Como funciona o WiFi?",
        "Obrigado pela ajuda!"
    ]
    
    for message in test_messages:
        print(f"\n📝 Testing message: '{message}'")
        
        try:
            response = await agent_manager.process_message(
                tenant_id=tenant_id,
                message=message,
                whatsapp_number="5511999999999",
                conversation_id="test-conv-001"
            )
            
            print(f"✅ Response: {response.get('message', 'No response')}")
            print(f"📊 Success: {response.get('success', False)}")
            
        except Exception as e:
            print(f"❌ Error processing message: {e}")

async def test_database_connection():
    """Test database connection"""
    print("\n🧪 Testing Database Connection")
    print("=" * 40)
    
    try:
        # Test tenant lookup
        tenant = await db_service.get_tenant("test-tenant-123")
        
        if tenant:
            print("✅ Database connection successful")
            print(f"📊 Tenant found: {tenant.get('id', 'Unknown')}")
        else:
            print("⚠️  No tenant found (this is expected for test tenant)")
            
        # Test agent configurations
        configs = await db_service.get_agent_configurations("test-tenant-123")
        print(f"📊 Agent configurations: {len(configs)}")
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")

async def main():
    """Main test function"""
    print("🚀 LangGraph Agent Service Test Suite")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Validate environment
    required_vars = ["OPENAI_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please set these variables in your .env file")
        return
    
    print("✅ Environment variables validated")
    
    # Run tests
    await test_database_connection()
    await test_agent_initialization()
    await test_message_processing()
    
    print("\n🎉 Test suite completed!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
