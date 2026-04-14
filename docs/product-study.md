# Estudo de Produto: PMS para Anfitriões Individuais

## Contexto do Produto

Produto novo, independente, voltado a **anfitriões individuais** com 1-10 propriedades no mercado brasileiro. O objetivo é criar um PMS moderno e acessível que se diferencia dos players atuais (Stays.net, Hiper, etc.) com foco em:

- **WhatsApp como canal principal** — tanto para o hóspede quanto para o anfitrião
- **Sistema proativo** — o PMS avisa o anfitrião o que precisa ser feito (não o contrário)
- **Automações práticas** que entregam resultado sem exigir aprendizado de um painel complexo
- **Preço acessível** para o pequeno anfitrião brasileiro

---

## 1. Análise Competitiva

### Players globais

| Player | Público | Preço | Ponto fraco |
|--------|---------|-------|-------------|
| **Guesty** | Grandes gestores | $$$$ | Complexo, caro demais para PF |
| **Hostaway** | Médio/grande | $$$ | Interface pesada, sem foco Brasil |
| **Lodgify** | Pequeno/médio | $$ | Channel manager fraco para BR |
| **Hostfully** | Pequeno | $$ | Sem integração WhatsApp |
| **Beds24** | Técnicos | $ | Interface ultrapassada |
| **Smoobu** | Pequeno EU | $ | Pouca presença no Brasil |

### Players Brasil

| Player | Foco | Preço estimado | Gaps identificados |
|--------|------|---------------|-------------------|
| **Stays.net** | Gestoras (20+ imóveis) | R$299–R$999+/mês | Setup complexo, WhatsApp como addon, não proativo, muito caro para PF |
| **Omnibees** | Hotéis | Alto | Não serve short-term rental |
| **Hiper** | Pequeno anfitrião | R$99–R$199/mês | Channel manager limitado, sem IA, interface datada |
| **Reserva Fácil** | Pequeno anfitrião | R$99/mês | Funcionalidades básicas, sem automações |

### Gaps de mercado (oportunidade real)

1. **Nenhum player** usa WhatsApp como canal de gestão para o **anfitrião** — todos usam só para o hóspede
2. Sistemas são **reativos** — o anfitrião precisa entrar no painel para descobrir o que aconteceu
3. **Onboarding complexo**: Stays.net leva dias para configurar
4. **Nenhum tem IA nativa** integrada no core (apenas chatbots básicos como addon)
5. **Check-in digital** automatizado é raro ou caro nos players acessíveis
6. Players BR não têm **alertas inteligentes** sobre ações que o anfitrião precisa tomar
7. Falta um produto que **fale a língua do pequeno anfitrião** — simples, direto, no WhatsApp

---

## 2. Proposta de Valor

> **"O PMS que trabalha pra você enquanto você dorme — tudo pelo WhatsApp."**

Não é mais um painel com 50 abas. É um assistente que:
- Avisa quando você pode **ganhar mais** (datas ociosas, preço abaixo da concorrência, anúncio sem foto)
- Responde automaticamente às **perguntas de interessados** antes de reservar
- Avisa quando chega uma reserva nova
- Cobra os documentos do hóspede automaticamente
- Manda as instruções de acesso sem você precisar fazer nada
- Te envia um relatório toda segunda-feira
- Avisa quando você precisa agir (hóspede não fez check-in, avaliação pendente, calendário vazio)

---

## 3. Lista de Features

### MVP — Fase 1 (lançamento)

#### Pré-Reserva: Vendas e Conversão

- **Resposta automática a consultas via WhatsApp** — quando um interessado envia mensagem antes de reservar, o sistema responde com disponibilidade, preços e informações do imóvel
- Envio automático de **link de reserva direta** com proposta de desconto para fechar fora da OTA
- **Alerta de calendário ocioso** — notifica o anfitrião quando há X dias sem reserva com sugestão de ação (reduzir preço, ativar promoção, impulsionar anúncio)
- **Alerta de preço fora de mercado** — compara a tarifa atual com concorrentes próximos e alerta quando está acima da média para as datas disponíveis
- **Análise de anúncio** — verifica se o anúncio no Airbnb/Booking tem fotos suficientes, descrição completa e avaliações recentes; alerta o anfitrião sobre pontos de melhoria
- **Gestão de perguntas frequentes** — responde automaticamente a perguntas comuns de pré-reserva (aceita pets? tem estacionamento? qual o mínimo de noites?)
- **Coleta de avaliações** — solicita automaticamente avaliação após checkout, com texto sugerido ao hóspede para aumentar conversão

#### Sincronização de Calendário

- Importação de reservas via **iCal** (Airbnb, Booking.com, VRBO — sem precisar de parceria)
- Calendário unificado com todas as plataformas
- Atualização automática a cada 15 minutos
- Bloqueio manual de datas
- Visualização: data de entrada/saída, hóspede, plataforma, valor, status

#### Check-in Digital

- Envio automático de mensagem de boas-vindas via WhatsApp ao hóspede (D-3)
- Solicitação e coleta de documentos (RG, CPF, Passaporte) via WhatsApp
- Validação básica do documento recebido
- Envio das instruções de acesso após check-in aprovado
- Suporte automatizado a perguntas frequentes (WiFi, endereço, horários)

#### Comunicação Proativa com o Anfitrião (via WhatsApp)

- Alerta de **nova reserva** criada em qualquer plataforma
- Alerta de **check-in pendente** (hóspede ainda não enviou documentos — D-1)
- Alerta de **saída no dia** (hóspede sai hoje, limpeza necessária)
- Alerta de **entrada no dia** (hóspede entra hoje)
- Relatório **semanal** toda segunda-feira (ocupação, receita, próximas reservas)
- Alerta de **ação requerida** ("Hóspede João ainda não fez check-in no AP 302")
- Alerta de **calendário ocioso** (X dias sem reserva — pode impulsionar anúncio)

#### Cadastro Básico

- Cadastro de propriedades (nome, endereço, capacidade, fotos, regras da casa)
- Cadastro e histórico de hóspedes
- Configuração do canal WhatsApp da propriedade

#### Dashboard Simples

- Ocupação do mês
- Receita do mês (estimada a partir das reservas)
- Próximas entradas e saídas
- Status do check-in por reserva

---

### Produto Completo — Fase 2

#### Pré-Reserva Avançado

- **Motor de precificação dinâmica por IA** — sugere ou aplica automaticamente ajustes de preço baseados em: taxa de ocupação local, eventos na cidade, sazonalidade histórica e demanda em tempo real
- **Otimização de anúncio por IA** — reescreve título e descrição do anúncio para maximizar conversão, com teste A/B
- **Funil de reserva direta** — página própria do anfitrião com calendário, fotos, avaliações e checkout com PIX; permite capturar hóspedes recorrentes sem pagar comissão
- **CRM de interessados** — registra todos os contatos que consultaram mas não reservaram, com possibilidade de retargeting via WhatsApp
- **Promoções inteligentes** — cria automaticamente promoções de última hora para datas ociosas próximas (ex: 15% off para fins de semana com menos de 7 dias)
- **Monitoramento de concorrentes** — acompanha preços de imóveis similares na região e alerta quando há oportunidade de posicionamento

#### Channel Manager Real (sincronização bidirecional)

- Integração via API oficial com **Airbnb** (requer parceria)
- Integração via API oficial com **Booking.com** (Connectivity Partner)
- Integração com **VRBO / Expedia**
- Integração com **Google Vacation Rentals**
- Motor de **reserva direta** (link próprio com calendário + PIX)
- Sincronização de preços e disponibilidade em tempo real (evitar double booking)

#### Revenue Management

- Sugestão de preço por IA (ocupação, sazonalidade, concorrência)
- Regras de precificação automática por período
- Tarifa de limpeza configurável por propriedade
- Preços especiais por temporada

#### Gestão de Operações

- **Limpeza:** notificação automática para a diarista após cada checkout
- **Checklist de vistoria:** entrada e saída com fotos
- **Manutenção:** registro de chamados e acompanhamento
- **Fechaduras smart:** integração com TTLock, Yale, Keymaster — geração de código por reserva

#### Financeiro

- Registro de receitas por reserva, propriedade e plataforma
- Registro de despesas (limpeza, manutenção, plataformas)
- Relatório de resultado por propriedade por período
- Extrato de comissões por OTA
- **PIX** para pagamentos no motor de reserva direta
- Emissão de **NF-e** (nota fiscal eletrônica)

#### Experiência do Hóspede Avançada

- Envio de guia digital da propriedade via WhatsApp
- Coleta de avaliação pós-checkout de forma automática
- **Upsell automático**: early check-in, late check-out, serviços extras
- Suporte com IA para dúvidas sobre a estadia
- Escalonamento para atendimento humano quando necessário

---

### Fase 3 — Escala

- Portal do proprietário (para gestoras que administram imóveis de terceiros)
- Split de receita automático anfitrião/proprietário
- **Telegram** como canal alternativo ao WhatsApp
- Aplicativo mobile (iOS e Android) ou PWA
- Integrações com OTAs regionais (Decolar, AlugueTemporada, Temporada Livre)
- Revenue management com benchmarking de mercado em tempo real

---

## 4. Arquitetura Técnica

### Stack recomendado

```
Backend:     Node.js (NestJS) — arquitetura modular monolítica
Database:    PostgreSQL (Supabase)
Frontend:    Next.js (web dashboard)
WhatsApp:    Evolution API (self-hosted)
IA/LLM:      Claude API (claude-haiku-4-5 para agentes de automação)
Queue:       BullMQ (Redis) para tasks assíncronas
Storage:     Supabase Storage para documentos e fotos
```

### Esquema de banco de dados (núcleo)

```sql
-- Anfitriões (tenants)
tenants
  id, name, whatsapp_number, plan, created_at

-- Propriedades
properties
  id, tenant_id, name, address, capacity,
  checkin_time, checkout_time,
  wifi_name, wifi_password, access_instructions,
  rules, photos[]

-- Conexões com OTAs
ota_connections
  id, property_id, platform (airbnb|booking|vrbo|direct),
  ical_url, api_key, api_secret, last_sync_at

-- Reservas
reservations
  id, property_id, platform, external_id,
  guest_name, guest_phone, guest_email,
  checkin_date, checkout_date, total_amount, nights,
  status (confirmed|cancelled|pending),
  checkin_status (pending|docs_sent|docs_received|approved)

-- Hóspedes
guests
  id, name, phone, email, cpf, document_type,
  document_number, document_photo_url, validated_at

-- Bloqueios manuais
calendar_blocks
  id, property_id, start_date, end_date, reason

-- Tarefas de limpeza
cleaning_tasks
  id, reservation_id, assigned_to, scheduled_for, status, notes

-- Registros financeiros
financial_records
  id, property_id, reservation_id, type (revenue|expense),
  amount, category, date, notes

-- Fila de alertas para o anfitrião
owner_alerts
  id, tenant_id, type, message, scheduled_for, sent_at, status

-- Histórico de mensagens
message_logs
  id, reservation_id, direction (in|out), channel (whatsapp|telegram),
  content, sent_at
```

### Fluxo de sincronização iCal

```
CRON (a cada 15 min)
  → Para cada property com ota_connections
  → Busca URL iCal de cada plataforma
  → Faz parse do arquivo .ics
  → Compara com reservas existentes no banco
  → Cria/cancela/atualiza reservas
  → Dispara alertas para o anfitrião se houver mudanças
```

### Fluxo de check-in digital

```
Reserva criada (via iCal sync)
  → D-3: Envia mensagem de boas-vindas ao hóspede via WhatsApp
  → Hóspede envia foto do documento
  → IA valida o documento (qualidade, tipo, legibilidade)
  → Dados extraídos e salvos
  → D-0 (check-in): Envia código de acesso / instruções
  → Anfitrião notificado que check-in foi concluído
```

### Arquitetura de alertas proativos

```
Sistema de eventos (event-driven via BullMQ)

PRÉ-RESERVA (vendas):
  Evento: calendario_ocioso_7d      → Alerta + sugestão de ação ao anfitrião
  Evento: preco_acima_mercado       → Alerta de oportunidade de ajuste
  Evento: anuncio_incompleto        → Sugestão de melhoria do anúncio
  Evento: ultima_hora (D-3_vazio)   → Cria promoção automática

PÓS-RESERVA (operações):
  Evento: nova_reserva              → Notifica anfitrião
  Evento: D-3 antes check-in        → Envia boas-vindas ao hóspede
  Evento: D-1 antes check-in        → Verifica se docs foram enviados
  Evento: D-0 checkout              → Notifica sobre saída + agenda limpeza
  Evento: D+1 pos-checkout          → Solicita avaliação ao hóspede
  Evento: monday_9am                → Relatório semanal

Canal: WhatsApp (Evolution API) — primário
Canal: Telegram — alternativo (Fase 3)
```

### Integrações de Channel Manager — Prioridade

| # | Plataforma | Método | Requisito | Fase |
|---|-----------|--------|-----------|------|
| 1 | Airbnb | iCal | Nenhum | MVP |
| 2 | Booking.com | iCal | Nenhum | MVP |
| 3 | VRBO/Expedia | iCal | Nenhum | MVP |
| 4 | Airbnb | API oficial | Parceria Airbnb | Fase 2 |
| 5 | Booking.com | API oficial | Connectivity Partner | Fase 2 |
| 6 | Google Vacation Rentals | API | Via parceiro | Fase 3 |

---

## 5. Modelo de Negócio

### Preço sugerido

| Plano | Preço/mês | Propriedades | Features principais |
|-------|-----------|-------------|-------------------|
| **Starter** | R$79 | até 2 | iCal sync + check-in digital + alertas WhatsApp |
| **Pro** | R$149 | até 5 | + financeiro + limpeza + relatórios completos |
| **Growth** | R$249 | até 15 | + API oficial OTAs + motor de reserva direta + PIX |

> Comparação: Stays.net começa em R$299/mês focado em gestoras de 20+ imóveis.

### Métricas de sucesso (Fase 1)

- 20 anfitriões pagantes no primeiro mês
- Churn < 5%/mês
- NPS > 50
- Média de 2+ propriedades por anfitrião ativo

---

## 6. Roadmap de Desenvolvimento

### Fase 1 — MVP (10-12 semanas)

**Sprint 1-2: Fundação**
- Setup do projeto (banco, infra, autenticação)
- CRUD de propriedades
- Cadastro de conexões iCal por plataforma

**Sprint 3-4: Channel Manager Básico**
- Engine de parse de iCal
- Sincronização automática (cron a cada 15 min)
- Calendário unificado no dashboard
- Detecção de conflitos (double booking)

**Sprint 5-6: Check-in Digital e Comunicação com Hóspede**
- Fluxo de WhatsApp para o hóspede (boas-vindas, coleta de docs)
- Validação de documentos
- Envio automático de instruções de acesso
- Respostas automáticas a perguntas frequentes

**Sprint 7-8: Pré-Reserva e Alertas de Vendas**
- Resposta automática a consultas de interessados via WhatsApp
- Alerta de calendário ocioso com sugestão de ação
- Alerta de preço fora de mercado (análise básica)
- Análise de anúncio (checklist de qualidade)

**Sprint 9-10: Alertas Proativos para o Anfitrião**
- Engine de alertas (fila de eventos com BullMQ)
- Notificação de nova reserva
- Alertas D-1 / D-0 (check-in/checkout)
- Solicitação automática de avaliação pós-checkout
- Relatório semanal automático via WhatsApp

**Sprint 11-12: Beta e Onboarding**
- Interface web básica (dashboard + configurações)
- Onboarding guiado (cadastro de imóvel + conexão iCal em < 10 min)
- Testes com 5-10 anfitriões beta
- Ajustes baseados em feedback

### Fase 2 — Produto (12-16 semanas)

- API oficial Airbnb + Booking.com
- Motor de reserva direta + PIX
- Gestão de limpeza
- Financeiro completo (receitas + despesas + relatórios)
- Fechaduras smart (TTLock)
- Revenue management básico

### Fase 3 — Escala (ongoing)

- Telegram como canal alternativo
- Revenue management com IA e benchmarking
- Portal do proprietário (para gestoras)
- NF-e
- App mobile / PWA
- OTAs regionais (Decolar, AlugueTemporada)

---

## 7. Riscos e Mitigações

| Risco | Probabilidade | Mitigação |
|-------|--------------|-----------|
| Airbnb/Booking bloquearem iCal | Baixa | APIs públicas e estáveis há anos; parceria API em paralelo |
| Parceria API Airbnb demorar | Alta | Usar iCal no MVP — funcional e sem burocracia |
| Concorrência do Stays.net em preço | Média | Diferencial é proatividade e simplicidade, não só preço |
| Custo de WhatsApp (por mensagem) | Média | Otimizar frequência; incluir custo no pricing |
| Adoção lenta pelo público PF | Média | Onboarding guiado + trial de 30 dias gratuito |
