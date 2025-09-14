import os
import asyncio
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph_supervisor import create_supervisor
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_simple_supervisor():
    print("🧪 Teste Simples do Supervisor LangGraph")
    print("=======================================")
    
    # Criar agentes simples
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Agente Mike
    mike_prompt = """You are Mike, a document specialist. Help with document validation and check-in processes."""
    mike_agent = create_react_agent(
        model=model,
        tools=[],
        prompt=mike_prompt,
        name="mike"
    )
    
    # Agente Lara
    lara_prompt = """You are Lara, a general support specialist. Help with property information, amenities, and general questions."""
    lara_agent = create_react_agent(
        model=model,
        tools=[],
        prompt=lara_prompt,
        name="lara"
    )
    
    # Criar supervisor
    supervisor_prompt = """You are a Supervisor coordinating two specialists:

- mike: handles document validation, check-in processes, and document-related questions.
- lara: handles general support, property information, amenities, and general guest questions.

Your goal is to satisfy the user's intent efficiently.

Routing:
- If the request is about documents, check-in, or validation, use mike.
- If the request is about property info, amenities, general support, or recommendations, use lara.
- If the request is a simple greeting or basic question, respond directly.

Be decisive: when you have enough information, proceed with the appropriate agent without asking for confirmation."""
    
    supervisor = create_supervisor(
        agents=[mike_agent, lara_agent],
        model=model,
        prompt=supervisor_prompt,
        output_mode="full_history"
    ).compile()
    
    print("✅ Supervisor criado com sucesso!")
    
    # Testar com uma mensagem
    message = "Como funciona o estacionamento do hotel?"
    print(f"\n📝 Mensagem: {message}")
    
    input_data = {"messages": [HumanMessage(content=message)]}
    result = supervisor.invoke(input_data)
    
    print(f"\n📊 Resultado:")
    print(f"Número de mensagens: {len(result.get('messages', []))}")
    
    for i, msg in enumerate(result.get('messages', [])):
        print(f"Mensagem {i}: {type(msg).__name__} - {msg.content[:200]}...")
    
    # Verificar se a última mensagem é uma resposta completa
    messages = result.get("messages", [])
    if messages:
        last_message = messages[-1]
        print(f"\n✅ Última mensagem: {last_message.content[:100]}...")
        print(f"Tipo: {type(last_message).__name__}")
        
        if len(last_message.content) > 10:
            print("🎉 Supervisor executou o agente automaticamente!")
        else:
            print("❌ Supervisor apenas fez roteamento, não executou o agente")

if __name__ == "__main__":
    asyncio.run(test_simple_supervisor())
