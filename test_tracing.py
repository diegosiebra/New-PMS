#!/usr/bin/env python3
"""
Script de teste para demonstrar o tracing automático do LangGraph
"""

import os
import asyncio
from dotenv import load_dotenv
from agents import agent_manager

# Carregar variáveis de ambiente
load_dotenv()

async def test_tracing():
    """Testa o tracing automático dos agentes"""
    
    print("🔍 Testando Tracing Automático do LangGraph")
    print("=" * 50)
    
    # Configurar tenant para teste
    tenant_id = "e8136054-c7a8-4c4e-b6cc-58b86483c337"
    message = "Como funciona o estacionamento do hotel?"
    whatsapp_number = "5511999999999"
    
    print(f"📝 Mensagem: {message}")
    print(f"🏢 Tenant: {tenant_id}")
    print(f"📱 WhatsApp: {whatsapp_number}")
    print()
    
    # Processar mensagem com tracing automático
    print("🚀 Processando mensagem com agentes...")
    print("📊 Tracing automático ativado - você verá:")
    print("   - Qual agente foi escolhido pelo supervisor")
    print("   - Quais tools foram executados")
    print("   - Tempo de execução de cada step")
    print("   - Input/output de cada chamada")
    print()
    
    try:
        response = await agent_manager.process_message(
            tenant_id=tenant_id,
            message=message,
            whatsapp_number=whatsapp_number,
            conversation_id="test_tracing_001"
        )
        
        print("✅ Processamento concluído!")
        print(f"📤 Resposta: {response.get('message', 'Sem resposta')}")
        print(f"📊 Status: {response.get('success', False)}")
        
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    asyncio.run(test_tracing())
