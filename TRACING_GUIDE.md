# 🔍 Guia de Tracing Automático - LangGraph

Este guia mostra como configurar tracing automático no LangGraph para visualizar qual agente foi chamado, quais tools foram executados, sem precisar escrever logs manuais.

## 🚀 Opções de Tracing

### 1. **Tracing no Console (Ativado por padrão)**

O tracing no console já está configurado e ativo quando `LANGGRAPH_DEBUG=true` no `.env`.

**O que você verá automaticamente:**
- ✅ Qual agente foi escolhido pelo supervisor
- ✅ Quais tools foram executados por cada agente
- ✅ Input/output de cada chamada LLM
- ✅ Tempo de execução de cada step
- ✅ Erros e exceções detalhadas

### 2. **LangSmith (Opcional - Observabilidade Avançada)**

Para usar o LangSmith, adicione ao seu `.env`:

```bash
# LangSmith Tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_PROJECT=reservaflow-agent-service
```

**Benefícios do LangSmith:**
- 🌐 Interface web para visualizar traces
- 📊 Métricas de performance
- 🔍 Debugging avançado
- 📈 Análise de custos
- 🎯 Comparação de execuções

## 🧪 Como Testar

### Teste 1: Console Tracing
```bash
# 1. Certifique-se que LANGGRAPH_DEBUG=true no .env
# 2. Execute o servidor
python run.py

# 3. Envie uma mensagem via webhook
curl -X POST http://localhost:3001/api/webhook/evolution \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: e8136054-c7a8-4c4e-b6cc-58b86483c337" \
  -d '{
    "event": "MESSAGES_UPSERT",
    "instance": "test-instance",
    "data": {
      "key": {
        "remoteJid": "5511999999999@s.whatsapp.net",
        "fromMe": false,
        "id": "msg_test"
      },
      "message": {
        "conversation": "Como funciona o estacionamento do hotel?"
      }
    }
  }'
```

### Teste 2: Script de Teste
```bash
python test_tracing.py
```

## 📊 O que Você Verá no Console

```
🔍 Testando Tracing Automático do LangGraph
==================================================
📝 Mensagem: Como funciona o estacionamento do hotel?
🏢 Tenant: e8136054-c7a8-4c4e-b6cc-58b86483c337
📱 WhatsApp: 5511999999999

🚀 Processando mensagem com agentes...
📊 Tracing automático ativado - você verá:
   - Qual agente foi escolhido pelo supervisor
   - Quais tools foram executados
   - Tempo de execução de cada step
   - Input/output de cada chamada

[LangGraph Trace]
├── Supervisor Decision: "lara"
├── Agent: Lara Agent
│   ├── Tool Call: get_property_info
│   │   ├── Input: {"query": "estacionamento"}
│   │   ├── Output: "Informações sobre estacionamento..."
│   │   └── Duration: 1.2s
│   └── LLM Call: Generate Response
│       ├── Input: "Como funciona o estacionamento..."
│       ├── Output: "O estacionamento funciona..."
│       └── Duration: 0.8s
└── Total Duration: 2.1s

✅ Processamento concluído!
📤 Resposta: O estacionamento funciona das 6h às 22h...
📊 Status: True
```

## 🛠️ Configurações Avançadas

### Personalizar Logs
```python
# Em supervisor_agent.py, você pode personalizar o tracing:
def invoke(self, input_data):
    callbacks = []
    
    # Console tracing (já configurado)
    if os.getenv("LANGGRAPH_DEBUG", "false").lower() == "true":
        callbacks.append(ConsoleCallbackHandler())
    
    # Adicionar outros callbacks se necessário
    # callbacks.append(CustomCallbackHandler())
    
    config = {"callbacks": CallbackManager(callbacks)}
    result = self.supervisor.invoke(input_data, config=config)
    return result
```

### Filtrar Informações
```python
# Para mostrar apenas informações específicas:
class FilteredCallbackHandler(ConsoleCallbackHandler):
    def on_tool_start(self, serialized, input_str, **kwargs):
        print(f"🔧 Tool: {serialized['name']}")
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        print(f"🤖 LLM: {serialized['name']}")
```

## 🎯 Benefícios

✅ **Zero configuração**: Funciona automaticamente
✅ **Informações completas**: Vê todo o fluxo de execução
✅ **Debugging fácil**: Identifica problemas rapidamente
✅ **Performance**: Monitora tempo de execução
✅ **Flexível**: Pode ser desabilitado facilmente

## 🔧 Troubleshooting

**Problema**: Não vejo traces no console
**Solução**: Verifique se `LANGGRAPH_DEBUG=true` no `.env`

**Problema**: Traces muito verbosos
**Solução**: Configure `LANGGRAPH_LOG_LEVEL=info` para menos detalhes

**Problema**: LangSmith não funciona
**Solução**: Verifique se `LANGCHAIN_API_KEY` está correto
