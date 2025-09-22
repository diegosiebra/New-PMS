import os
import asyncio
from dotenv import load_dotenv
from agents import agent_manager
from langchain_core.messages import HumanMessage
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_supervisor_debug():
    print("🔍 Debug do Supervisor")
    print("======================")
    
    tenant_id = "e8136054-c7a8-4c4e-b6cc-58b86483c337"
    message = "Como funciona o estacionamento do hotel?"
    
    print(f"📝 Mensagem: {message}")
    print(f"🏢 Tenant: {tenant_id}")
    
    # Ativar debug para ver o tracing no console
    os.environ["LANGGRAPH_DEBUG"] = "true"
    
    # Verificar se os agentes estão inicializados
    print("\n🔍 Verificando agentes...")
    agent_info = agent_manager.get_agent_info(tenant_id)
    print(f"Agentes disponíveis: {len(agent_info['agents'])}")
    for agent in agent_info['agents']:
        print(f"  - {agent.get('name', 'Unknown')}: {agent.get('description', 'No description')}")
    
    print(f"Supervisor disponível: {agent_info['supervisor']}")
    
    # Testar o supervisor diretamente
    if tenant_id in agent_manager.supervisors:
        print("\n🧪 Testando supervisor diretamente...")
        supervisor = agent_manager.supervisors[tenant_id]
        
        # Testar com uma mensagem simples
        input_data = {"messages": [HumanMessage(content=message)]}
        thread_id = f"{tenant_id}:test_user"
        result = supervisor.invoke(input_data, thread_id=thread_id)
        
        print(f"Resultado do supervisor: {result}")
        
        # Verificar mensagens
        messages = result.get("messages", [])
        print(f"Número de mensagens: {len(messages)}")
        
        for i, msg in enumerate(messages):
            print(f"Mensagem {i}: {type(msg).__name__} - {msg.content[:100]}...")
    else:
        print("❌ Supervisor não encontrado!")
    
    # Testar o processamento completo
    print("\n🚀 Testando processamento completo...")
    response = await agent_manager.process_message(
        tenant_id=tenant_id,
        message=message,
        whatsapp_number="5511999999999",
        conversation_id="test_debug_001"
    )
    
    print("\n✅ Resultado:")
    print(f"📤 Resposta: {response.get('message')}")
    print(f"📊 Status: {response.get('success')}")

if __name__ == "__main__":
    asyncio.run(test_supervisor_debug())
