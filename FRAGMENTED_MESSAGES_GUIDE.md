# Guia de Mensagens Fragmentadas (Picotadas)

Este documento explica como o sistema lida com mensagens fragmentadas vindas da Evolution API (WhatsApp).

## Visão Geral

O WhatsApp frequentemente divide mensagens longas em múltiplas partes devido a limitações de tamanho. O sistema implementa um buffer inteligente para detectar e reconstituir essas mensagens fragmentadas antes de processá-las com os agentes.

## Tipos de Fragmentação Detectados

### 1. Fragmentos Numerados
Mensagens com indicadores como `[1/3]`, `[2/3]`, `[3/3]`:

```
[1/3] Esta é a primeira parte da mensagem que foi
[2/3] dividida em três partes pelo WhatsApp
[3/3] e precisa ser reconstituída corretamente.
```

### 2. Fragmentos de Continuação
Mensagens que terminam com `...` ou `…`:

```
Esta mensagem foi dividida automaticamente pelo WhatsApp...
e precisa ser reconstituída para formar uma mensagem completa...
sem perder nenhuma informação importante.
```

### 3. Fragmentos por Tamanho
Mensagens muito longas (>1000 caracteres) que são divididas automaticamente pelo WhatsApp.

## Como Funciona

### 1. Detecção Automática
O sistema analisa cada mensagem recebida e detecta automaticamente se é um fragmento baseado em padrões conhecidos.

### 2. Buffer Inteligente
- Mensagens fragmentadas são armazenadas em um buffer temporário
- Cada conversação tem seu próprio buffer identificado por: `tenant_id:whatsapp_number:conversation_id`
- Timeout padrão de 30 segundos para mensagens incompletas

### 3. Reconstituição
- Quando todos os fragmentos são recebidos, a mensagem é reconstituída
- A mensagem completa é então processada pelos agentes
- O buffer é limpo automaticamente

### 4. Limpeza Automática
- Task em background limpa buffers expirados a cada 10 segundos
- Buffers incompletos são removidos após o timeout

## Arquivos Implementados

### `message_buffer_service.py`
Serviço principal que gerencia o buffer de mensagens fragmentadas:
- `MessageBufferService`: Classe principal
- `process_message()`: Processa mensagens e detecta fragmentos
- `force_complete_message()`: Força conclusão de mensagens incompletas
- `get_active_buffers_count()`: Monitora buffers ativos

### `models.py`
Modelos de dados adicionados:
- `FragmentedMessage`: Representa uma mensagem sendo reconstituída
- `MessageFragment`: Fragmento individual

### `webhook_service.py`
Modificado para integrar o buffer:
- Mensagens passam pelo buffer antes do processamento
- Só processa mensagens completas
- Logs detalhados do processo

### `main.py`
Endpoints adicionados para monitoramento:
- `GET /api/message-buffers/status`: Status dos buffers
- `POST /api/message-buffers/{tenant_id}/force-complete`: Força conclusão

## Endpoints de Monitoramento

### Status dos Buffers
```bash
GET /api/message-buffers/status
```

Resposta:
```json
{
  "success": true,
  "data": {
    "active_buffers_count": 3,
    "buffer_details": [
      {
        "buffer_key": "tenant1:5511999999999:conv123",
        "fragments_count": 2,
        "total_fragments": 3,
        "age_seconds": 15.5,
        "is_complete": false
      }
    ],
    "status": "healthy"
  }
}
```

### Forçar Conclusão
```bash
POST /api/message-buffers/{tenant_id}/force-complete
```

Parâmetros:
- `whatsapp_number`: Número do WhatsApp
- `conversation_id`: ID da conversa

## Testando o Sistema

Execute o script de teste:
```bash
python test_fragmented_messages.py
```

Este script testa:
- Fragmentos numerados
- Fragmentos de continuação
- Fragmentos por tamanho
- Cenários mistos
- Monitoramento de buffers
- Forçar conclusão

## Configurações

### Timeout de Buffer
Padrão: 30 segundos
Modificável em `FragmentedMessage.timeout_seconds`

### Limite de Caracteres
Padrão: 1000 caracteres para detecção de fragmentos por tamanho
Modificável em `_detect_fragmented_message()`

### Limpeza de Buffers
Intervalo: 10 segundos
Modificável em `_cleanup_expired_buffers()`

## Logs e Monitoramento

O sistema gera logs detalhados para:
- Detecção de fragmentos
- Criação de buffers
- Conclusão de mensagens
- Limpeza de buffers expirados
- Erros no processamento

Exemplo de logs:
```
INFO - Buffering numbered fragment 1/3 for tenant1:5511999999999:conv123
INFO - Completed numbered fragmented message for tenant1:5511999999999:conv123
INFO - Expired fragmented message buffer: tenant1:5511999999999:conv456
```

## Tratamento de Erros

- Mensagens malformadas são processadas como mensagens normais
- Buffers corrompidos são limpos automaticamente
- Timeouts previnem acúmulo de buffers órfãos
- Fallback para mensagens regulares em caso de erro

## Benefícios

1. **Processamento Correto**: Mensagens fragmentadas são reconstituídas antes do processamento
2. **Eficiência**: Evita processamento parcial de mensagens incompletas
3. **Robustez**: Sistema tolerante a falhas com limpeza automática
4. **Monitoramento**: Visibilidade completa do estado dos buffers
5. **Flexibilidade**: Suporte a diferentes tipos de fragmentação

## Considerações de Performance

- Buffers são mantidos em memória (não persistidos)
- Limpeza automática previne vazamentos de memória
- Timeout configurável para diferentes cenários
- Monitoramento de saúde do sistema

## Troubleshooting

### Buffer não está sendo limpo
- Verifique se a task de limpeza está rodando
- Monitore logs de limpeza
- Use endpoint de status para verificar buffers ativos

### Mensagens não sendo reconstituídas
- Verifique padrões de detecção
- Monitore logs de detecção de fragmentos
- Teste com diferentes tipos de fragmentação

### Performance degradada
- Monitore número de buffers ativos
- Ajuste timeout se necessário
- Verifique logs de limpeza automática
