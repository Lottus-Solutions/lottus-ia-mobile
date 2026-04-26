# Ecossistema de IA - Biblioteca Escolar (Flask + Gemini)

## Fase 1 - Arquitetura completa

A arquitetura foi desenhada em camadas para separar responsabilidades:

- app: bootstrap, configuracao e registro do Flask
- routes: contratos HTTP e validacao de entrada
- agents: orquestracao da inteligencia de negocio
- repositories: acesso SQL direto ao MySQL
- services: integracao externa (Gemini)
- prompts: instrucoes versionadas para cada tarefa de IA
- models: DTOs de resposta
- utils: utilitarios de parsing e carregamento de prompt

Fluxo por endpoint:

1. Route valida entrada e chama o agent correto.
2. Agent busca dados no banco via repositories.
3. Agent monta payload contextual e chama GeminiService.
4. Resultado e persistencia (quando aplicavel) sao retornados.

## Fase 2 - Estrutura de pastas

```
/app
/routes
/services
/agents
/repositories
/models
/utils
/prompts
/sql
/tests
```

## Fase 3 - Codigo Flask inicial funcionando

- Healthcheck: `GET /health`
- Swagger UI: `GET /docs`
- OpenAPI JSON: `GET /openapi.json`
- Endpoints IA:
  - `POST /perfil-leitura`
  - `POST /recomendar`
  - `POST /chat-reforco`

## Fase 4 - Integracao Gemini

Implementada com SDK oficial atualizado:

- Biblioteca: `google-genai`
- Modelo padrao: `gemini-2.5-flash`
- Classe principal: `services/gemini_service.py`
- Metodos:
  - `gerar_texto()`
  - `analisar_perfil()`
  - `recomendar()`
  - `transcrever_audio()`

Se `GEMINI_API_KEY` nao estiver definida, o sistema usa fallback local para desenvolvimento.

## Fase 5 - Agentes completos

- ProfileAgent
  - Consolida aluno, historico, categorias, frequencia e atrasos
  - Gera perfil textual curto
  - Salva em `perfil_leitura`

- RecommendationAgent
  - Usa perfil salvo + historico + livros nao lidos
  - Evita repeticao
  - Prioriza disponibilidade e aderencia
  - Retorna 3 recomendacoes

- ReinforcementChatAgent
  - Aceita texto ou audio
  - Transcreve audio via Gemini
  - Retorna orientacao pedagogica focada em leitura

## Fase 6 - Queries baseadas no database.sql

Tabelas reutilizadas diretamente:

- `alunos`
- `turmas`
- `emprestimos`
- `livros`
- `metas` (pronto para expansao)

Nova tabela criada por necessidade de persistencia:

- `perfil_leitura` (arquivo `sql/001_create_perfil_leitura.sql`)

## Fase 7 - Testes com exemplos reais

Arquivo: `tests/test_endpoints.py`

Cobertura inicial:

- `test_perfil_leitura_ok`
- `test_recomendar_ok`
- `test_chat_reforco_ok`

## Como executar

1. Criar ambiente virtual.
2. Instalar dependencias:
   `pip install -r requirements.txt`
3. Configurar variaveis com base no `.env.example`.
4. Garantir que o MySQL esteja ativo e com `database.sql` aplicado.
5. Rodar API:
   `python run.py`
6. Abrir a documentacao interativa:
  `http://localhost:5000/docs`

## Exemplos de chamada

### 1) Perfil de leitura

```bash
curl -X POST http://localhost:5000/perfil-leitura \
  -H "Content-Type: application/json" \
  -d '{"aluno_id": 1}'
```

### 2) Recomendacoes

```bash
curl -X POST http://localhost:5000/recomendar \
  -H "Content-Type: application/json" \
  -d '{"aluno_id": 1}'
```

### 3) Chat de reforco com texto

```bash
curl -X POST http://localhost:5000/chat-reforco \
  -F "aluno_id=1" \
  -F "texto=Meu filho esta mal em matematica"
```

### 4) Chat de reforco com audio

```bash
curl -X POST http://localhost:5000/chat-reforco \
  -F "aluno_id=1" \
  -F "audio=@./exemplo_audio.mp3"
```

## Melhorias recomendadas para proxima iteracao

1. Adicionar autenticacao JWT nos endpoints.
2. Registrar observabilidade (logs estruturados + metricas).
3. Criar cache de recomendacoes para reduzir latencia e custo.
4. Incluir job assicrono para processamento de audio pesado.
5. Expandir testes com banco de integracao e cenarios de erro.
