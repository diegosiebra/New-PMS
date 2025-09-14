#!/usr/bin/env python3
"""
Teste simples do supervisor seguindo o padrão do exemplo
"""

import asyncio
from dotenv import load_dotenv
from agents import agent_manager
from langchain_core.messages import HumanMessage

# Carregar variáveis de ambiente
load_dotenv()

async def test_simple_supervisor():
    """Testa o supervisor de forma simples como no exemplo"""
    
    print("🧪 Teste Simples do Supervisor")
    print("=" * 40)
    
    # Configurar tenant para teste
    tenant_id = "e8136054-c7a8-4c4e-b6cc-58b86483c337"
    message = "Como funciona o estacionamento do hotel?"
    
    print(f"📝 Mensagem: {message}")
    print(f"🏢 Tenant: {tenant_id}")
    print()
    
    try:
        # Processar mensagem - formato simples como no exemplo
        response = await agent_manager.process_message(
            tenant_id=tenant_id,
            message=message,
            whatsapp_number="5511999999999",
            conversation_id="test_simple_001"
        )
        
        print("✅ Resultado:")
        print(f"📤 Resposta: {response.get('message', 'Sem resposta')}")
        print(f"📊 Status: {response.get('success', False)}")
        
        # Mostrar todas as mensagens como no exemplo
        if response.get('success'):
            print("\n📋 Histórico de Mensagens:")
            # Aqui você poderia iterar pelas mensagens se necessário
            print("   - Mensagem processada com sucesso")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    asyncio.run(test_simple_supervisor())
