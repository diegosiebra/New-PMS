# Guia do Evolution API Service

Este documento explica como usar o serviço dedicado para comunicação com a Evolution API.

## Visão Geral

O `EvolutionAPIService` é uma classe dedicada que centraliza toda a comunicação com a Evolution API, separando essa responsabilidade do `WebhookService` e tornando o código mais modular e organizável.

## Arquitetura

### Separação de Responsabilidades

- **`WebhookService`**: Processa webhooks recebidos e coordena o fluxo
- **`EvolutionAPIService`**: Gerencia toda comunicação de saída com Evolution API
- **`MessageBufferService`**: Lida com mensagens fragmentadas
- **`AgentManager`**: Processa mensagens com agentes LangGraph

## Funcionalidades Implementadas

### 1. Envio de Mensagens de Texto
```python
result = await evolution_api_service.send_text_message(
    tenant_id="tenant123",
    whatsapp_number="5511999999999",
    message="Olá! Como posso ajudar?"
)
```

### 2. Envio de Mensagens de Mídia
```python
result = await evolution_api_service.send_media_message(
    tenant_id="tenant123",
    whatsapp_number="5511999999999",
    media_url="https://example.com/image.jpg",
    media_type="image",
    caption="Veja esta imagem!"
)
```

### 3. Envio de Mensagens Template
```python
result = await evolution_api_service.send_template_message(
    tenant_id="tenant123",
    whatsapp_number="5511999999999",
    template_name="welcome_template",
    parameters=["João", "12345"]
)
```

### 4. Status da Instância
```python
result = await evolution_api_service.get_instance_status("tenant123")
```

### 5. Marcar Mensagem como Lida
```python
result = await evolution_api_service.mark_message_as_read(
    tenant_id="tenant123",
    whatsapp_number="5511999999999",
    message_id="msg_123"
)
```

### 6. Obter Foto de Perfil
```python
result = await evolution_api_service.get_profile_picture(
    tenant_id="tenant123",
    whatsapp_number="5511999999999"
)
```

## Configuração

### Variáveis de Ambiente
```bash
EVOLUTION_API_KEY=your_evolution_api_key_here
```

### Configuração por Tenant
Cada tenant deve ter configuração no banco de dados:
```json
{
  "settings": {
    "evolution": {
      "baseUrl": "https://your-evolution-api.com",
      "instanceName": "your-instance-name"
    }
  }
}
```

## Endpoints Disponíveis

### Envio de Mídia
```bash
POST /api/evolution/{tenant_id}/send-media
```

Parâmetros:
- `whatsapp_number`: Número do WhatsApp
- `media_url`: URL da mídia
- `media_type`: Tipo da mídia (image, video, audio, document)
- `caption`: Legenda (opcional)

### Envio de Template
```bash
POST /api/evolution/{tenant_id}/send-template
```

Parâmetros:
- `whatsapp_number`: Número do WhatsApp
- `template_name`: Nome do template
- `parameters`: Lista de parâmetros (opcional)

### Status da Instância
```bash
GET /api/evolution/{tenant_id}/instance-status
```

### Marcar como Lida
```bash
POST /api/evolution/{tenant_id}/mark-read
```

Parâmetros:
- `whatsapp_number`: Número do WhatsApp
- `message_id`: ID da mensagem

### Foto de Perfil
```bash
GET /api/evolution/{tenant_id}/profile-picture?whatsapp_number=5511999999999
```

## Tratamento de Erros

Todos os métodos retornam um dicionário com:
```python
{
    "success": True/False,
    "message": "Descrição da operação",
    "error": "Mensagem de erro (se houver)",
    "response": {} # Resposta da Evolution API (se aplicável)
}
```

### Exemplos de Respostas

**Sucesso:**
```json
{
    "success": true,
    "message": "Message sent successfully",
    "response": {
        "key": {
            "remoteJid": "5511999999999@s.whatsapp.net",
            "fromMe": true,
            "id": "msg_123"
        }
    }
}
```

**Erro:**
```json
{
    "success": false,
    "error": "Evolution API error: 401 - Unauthorized"
}
```

## Logs e Monitoramento

O serviço gera logs detalhados para:
- Envio de mensagens
- Erros de comunicação
- Status de instâncias
- Operações de leitura

Exemplo de logs:
```
INFO - Message sent successfully to 5511999999999 for tenant tenant123
ERROR - Error sending message via EvolutionAPI: 401 - Unauthorized
INFO - Instance status retrieved for tenant tenant123
```

## Benefícios da Separação

### 1. **Modularidade**
- Código organizado em responsabilidades específicas
- Fácil manutenção e testes
- Reutilização em diferentes contextos

### 2. **Flexibilidade**
- Fácil adição de novos métodos Evolution API
- Configuração centralizada
- Tratamento de erro consistente

### 3. **Testabilidade**
- Serviço pode ser testado independentemente
- Mocking facilitado para testes unitários
- Isolamento de dependências

### 4. **Escalabilidade**
- Fácil adição de cache, retry, etc.
- Pool de conexões HTTP
- Rate limiting por tenant

## Uso nos Agentes

Os agentes podem usar o EvolutionAPIService através do WebhookService:

```python
# No agente
async def send_response(self, tenant_id: str, whatsapp_number: str, message: str):
    result = await self.webhook_service.send_response(tenant_id, whatsapp_number, message)
    return result

# Para mídia
async def send_media(self, tenant_id: str, whatsapp_number: str, media_url: str):
    result = await self.webhook_service.send_media_message(
        tenant_id, whatsapp_number, media_url, "image", "Veja esta imagem!"
    )
    return result
```

## Extensibilidade

### Adicionando Novos Métodos

1. Adicione o método no `EvolutionAPIService`
2. Adicione wrapper no `WebhookService` (se necessário)
3. Adicione endpoint no `main.py` (se necessário)
4. Documente o novo método

### Exemplo de Novo Método

```python
async def send_location(self, tenant_id: str, whatsapp_number: str, 
                      latitude: float, longitude: float, name: str = "") -> Dict[str, Any]:
    """Send location message via Evolution API"""
    try:
        config = await self.get_tenant_evolution_config(tenant_id)
        if not config:
            return {"success": False, "error": "Evolution API configuration not found"}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{config['base_url']}/message/sendLocation/{config['instance_name']}",
                headers={
                    "Content-Type": "application/json",
                    "apikey": config["api_key"],
                },
                json={
                    "number": whatsapp_number,
                    "latitude": latitude,
                    "longitude": longitude,
                    "name": name
                }
            )
            
            if response.status_code == 200:
                return {"success": True, "response": response.json()}
            else:
                return {"success": False, "error": f"API error: {response.status_code}"}
                
    except Exception as e:
        return {"success": False, "error": str(e)}
```

## Considerações de Performance

### Pool de Conexões
O serviço usa `httpx.AsyncClient()` para cada requisição. Para alta performance, considere:
- Pool de conexões reutilizável
- Rate limiting por tenant
- Cache de configurações

### Retry e Fallback
Para robustez, considere implementar:
- Retry automático em falhas temporárias
- Fallback para métodos alternativos
- Circuit breaker para instâncias instáveis

## Troubleshooting

### Problemas Comuns

1. **Erro 401 - Unauthorized**
   - Verifique `EVOLUTION_API_KEY`
   - Confirme se a chave está correta

2. **Erro 404 - Instance Not Found**
   - Verifique `instanceName` na configuração do tenant
   - Confirme se a instância existe na Evolution API

3. **Erro 500 - Internal Server Error**
   - Verifique logs da Evolution API
   - Confirme se a instância está funcionando

### Debugging

Use os logs para identificar problemas:
```bash
# Verificar logs de envio
grep "Message sent successfully" logs/app.log

# Verificar erros
grep "Error sending message" logs/app.log

# Verificar configuração
grep "Missing EvolutionAPI configuration" logs/app.log
```
