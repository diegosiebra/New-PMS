# LangGraph Agent Service (Python)

Serviço de agentes multi-agente usando LangGraph com supervisor oficial e agentes React.

## Características

- ✅ **Supervisor Oficial**: Usa `langgraph-supervisor` com `create_supervisor()`
- ✅ **Agentes React**: Usa `create_react_agent()` para agentes especializados
- ✅ **API FastAPI**: Endpoints REST para webhooks e gerenciamento
- ✅ **Integração Supabase**: Banco de dados para configurações e logs
- ✅ **Webhook EvolutionAPI**: Processamento de mensagens WhatsApp
- ✅ **Multi-tenant**: Suporte a múltiplos tenants

## Instalação

1. **Instalar dependências**:
```bash
pip install -r requirements.txt
```

2. **Configurar variáveis de ambiente**:
```bash
cp env_example.txt .env
# Editar .env com suas configurações
```

3. **Executar o serviço**:
```bash
python run.py
```

## Configuração

### Variáveis de Ambiente

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4o-mini

# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_SERVICE_KEY=your_supabase_service_key_here
DATABASE_URL=your_database_url_here

# Server Configuration
PORT=3001
HOST=0.0.0.0

# LangGraph Configuration
LANGGRAPH_DEBUG=true
LANGGRAPH_LOG_LEVEL=debug
```

### Configuração Dinâmica dos Agentes

Todas as configurações dos agentes são carregadas dinamicamente do banco de dados através da tabela `agent_configurations`:

#### Estrutura da Tabela

```sql
CREATE TABLE agent_configurations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id uuid NOT NULL,
    agent_type varchar NOT NULL,
    agent_name varchar NOT NULL,
    is_enabled boolean DEFAULT true,
    configuration jsonb,
    prompt text,
    tools jsonb,
    model varchar DEFAULT 'gpt-4o',
    created_at timestamp DEFAULT now(),
    updated_at timestamp DEFAULT now()
);
```

#### Configurações Suportadas

- **`prompt`**: Prompt personalizado para cada agente
- **`tools`**: Ferramentas específicas em formato JSON
- **`model`**: Modelo OpenAI específico para cada agente
- **`configuration`**: Configurações adicionais (timeout, language, etc.)
- **`is_enabled`**: Habilita/desabilita agentes dinamicamente

#### Script de Configuração

Use o script `setup_agent_configurations.sql` para configurar os agentes:

```bash
# Executar no Supabase SQL Editor ou psql
psql -d your_database -f setup_agent_configurations.sql
```

## Agentes

### Mike (Document Collection)
- **Arquivo**: `mike_agent.py`
- **Especialidade**: Documentos e check-in
- **Ferramentas Dinâmicas** (do banco de dados):
  - `validate_document`: Validar se documento está legível e completo
  - `register_document`: Registrar documento no sistema
- **Ferramentas Padrão** (fallback):
  - `validate_documents`: Validar documentos
  - `process_checkin`: Processar check-in
  - `get_required_documents`: Listar documentos necessários
- **Prompt**: Configurável via banco de dados
- **Modelo**: Configurável via banco de dados

### Lara (RAG Support)
- **Arquivo**: `lara_agent.py`
- **Especialidade**: Suporte geral e informações
- **Ferramentas Dinâmicas** (do banco de dados):
  - `search_knowledge_base`: Buscar informações na base de conhecimento
  - `get_reservation_data`: Obter dados específicos da reserva
  - `escalate_to_human`: Escalar para atendimento humano
- **Ferramentas Padrão** (fallback):
  - `get_property_info`: Informações sobre a propriedade
  - `get_house_rules`: Regras da casa
  - `get_amenities`: Amenidades disponíveis
- **Prompt**: Configurável via banco de dados
- **Modelo**: Configurável via banco de dados

### Supervisor
- **Arquivo**: `supervisor_agent.py`
- **Função**: Decidir qual agente processar cada mensagem
- **Implementação**: `langgraph-supervisor` oficial
- **Prompt**: Configurável via banco de dados
- **Modelo**: Configurável via banco de dados
- **Capacidades**: Adicionar/remover agentes dinamicamente

## API Endpoints

### Webhooks
- `POST /api/webhooks/evolution/{tenant_id}` - Webhook com tenant ID na URL
- `POST /api/webhook/evolution` - Webhook com tenant ID no header X-Tenant-ID

### Gerenciamento de Agentes
- `GET /api/agents/{tenant_id}` - Listar agentes do tenant
- `GET /api/agents/{tenant_id}/stats` - Estatísticas dos agentes
- `POST /api/agents/{tenant_id}/reload` - Recarregar agentes
- `GET /api/configurations/{tenant_id}` - Configurações dos agentes

### Health Check
- `GET /health` - Status do serviço

## Estrutura do Projeto

```
python-agent-service/
├── main.py              # API FastAPI principal
├── agents.py            # Gerenciador de agentes e supervisor
├── webhook_service.py   # Processamento de webhooks
├── database.py          # Serviço de banco de dados
├── models.py            # Tipos e modelos Pydantic
├── run.py               # Script de inicialização
├── requirements.txt     # Dependências Python
├── env_example.txt      # Exemplo de variáveis de ambiente
└── README.md           # Este arquivo
```

## Arquitetura Modular

### Vantagens da Estrutura Separada

1. **Modularidade**: Cada agente em seu próprio arquivo
2. **Manutenibilidade**: Fácil de modificar e estender
3. **Reutilização**: Agentes podem ser reutilizados em outros projetos
4. **Testabilidade**: Cada agente pode ser testado independentemente
5. **Escalabilidade**: Fácil adicionar novos agentes

### Estrutura dos Agentes

Cada agente segue o mesmo padrão:
- **Classe principal**: Contém a lógica do agente
- **Ferramentas**: Funções específicas do agente
- **Prompt**: Configurável via banco de dados
- **Métodos**: `get_agent()`, `get_info()`

## Uso

### 1. Inicializar Agentes
```python
from agents import agent_manager

# Inicializar agentes para um tenant
await agent_manager.initialize_tenant_agents("tenant-id")
```

### 2. Processar Mensagem
```python
# Processar mensagem com supervisor
response = await agent_manager.process_message(
    tenant_id="tenant-id",
    message="Preciso de ajuda com documentos",
    whatsapp_number="5511999999999",
    conversation_id="conv-123"
)
```

### 3. Webhook EvolutionAPI
```bash
curl -X POST "http://localhost:3001/api/webhook/evolution" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: tenant-id" \
  -d '{
    "event": "MESSAGES_UPSERT",
    "instance": "test-instance",
    "data": {
      "key": {
        "remoteJid": "5511999999999@s.whatsapp.net",
        "fromMe": false,
        "id": "msg_001"
      },
      "message": {
        "conversation": "Como funciona o check-in?"
      }
    }
  }'
```

## Diferenças da Implementação TypeScript

### Vantagens da Implementação Python

1. **Supervisor Oficial**: Usa `langgraph-supervisor` real, não implementação customizada
2. **Agentes React**: Usa `create_react_agent()` oficial do LangGraph
3. **Melhor Integração**: Aproveita toda a funcionalidade nativa do LangGraph
4. **Ferramentas Nativas**: Suporte completo a ferramentas e tool calling
5. **Documentação Oficial**: Segue exatamente os padrões da documentação LangGraph

### Funcionalidades Implementadas

- ✅ Supervisor com `create_supervisor()`
- ✅ Agentes com `create_react_agent()`
- ✅ Ferramentas nativas para cada agente
- ✅ Prompts configuráveis via banco de dados
- ✅ Logging completo de execuções
- ✅ API REST completa
- ✅ Suporte a webhooks EvolutionAPI
- ✅ Multi-tenant com configurações dinâmicas

## Desenvolvimento

### Executar em Modo Debug
```bash
LANGGRAPH_DEBUG=true python run.py
```

### Testar Agentes
```python
# Teste rápido
python -c "
import asyncio
from agents import agent_manager

async def test():
    await agent_manager.initialize_tenant_agents('test-tenant')
    result = await agent_manager.process_message('test-tenant', 'Olá!', '5511999999999')
    print(result)

asyncio.run(test())
"
```

## Logs

O serviço gera logs detalhados incluindo:
- Inicialização de agentes
- Processamento de mensagens
- Decisões do supervisor
- Execução de ferramentas
- Erros e exceções

## Suporte

Para questões ou problemas:
1. Verificar logs do serviço
2. Validar configurações de ambiente
3. Testar conectividade com Supabase e OpenAI
4. Verificar configurações de agentes no banco de dados
