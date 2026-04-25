<p align="center">
  <img src="https://img.shields.io/badge/Gemini_2.5_Flash-4285F4?style=for-the-badge&logo=google&logoColor=white" alt="Gemini"/>
  <img src="https://img.shields.io/badge/Pinecone-000000?style=for-the-badge&logo=pinecone&logoColor=white" alt="Pinecone"/>
  <img src="https://img.shields.io/badge/Next.js_16-000000?style=for-the-badge&logo=next.js&logoColor=white" alt="Next.js"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/Supabase-3FCF8E?style=for-the-badge&logo=supabase&logoColor=white" alt="Supabase"/>
  <img src="https://img.shields.io/badge/Cloud_Run-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white" alt="Cloud Run"/>
  <img src="https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white" alt="Vercel"/>
</p>

<h1 align="center">⬡ FonteCerta — Plataforma de Especialistas Virtuais</h1>

<p align="center">
  <strong>Assistente de IA multi-persona com RAG, controle de acesso a conhecimento e arquitetura serverless.</strong>
</p>

<p align="center">
  <em>Desenvolvido por <strong>Maylton Tavares</strong></em>
</p>

---

## 🏗️ Visão Geral

O **FonteCerta** é uma plataforma de inteligência artificial que transforma documentos em conhecimento acessível por meio de **especialistas virtuais com personalidades distintas**. Cada especialista possui identidade, regras de comportamento e acesso controlado a documentos específicos — tudo gerenciado por um painel administrativo.

### O que o sistema faz:

- 📄 **Ingere** catálogos, fichas técnicas, imagens e vídeos via upload
- 🧩 **Vetoriza** o conteúdo com embeddings de última geração (Gemini Embedding 2)
- 🔍 **Busca** semanticamente nos documentos via Pinecone Serverless
- 🤖 **Responde** com IA generativa (Gemini 2.5 Flash) usando RAG com re-ranking
- 🎭 **Adapta** a personalidade da resposta ao especialista selecionado

---

## 🎭 Arquitetura Multi-Persona

O diferencial do sistema é a **Plataforma de Especialistas Virtuais** — cada persona de IA tem:

| Atributo | Descrição |
|----------|-----------|
| 🎯 **Identidade** | System prompt customizado que define tom, expertise e abordagem |
| 📋 **Regras** | Até 15 regras de comportamento (ex: "sempre sugira o melhor produto") |
| 🌡️ **Temperatura** | Nível de criatividade calibrado por persona (0.0 a 1.0) |
| 🔐 **Acesso** | Público, logado ou admin — controla quem pode usar cada persona |
| 📁 **Conhecimento** | Filtro por documento — cada especialista consulta apenas o que foi autorizado |

### Especialistas Padrão

| Persona | Foco | Temp. |
|---------|------|-------|
| 🟢 **Vendedor Técnico** | Vendas consultivas, abordagem comercial, conversão | 0.5 |
| 🟥 **Engenheiro de Aplicação** | Especificações, normas ABNT/ISO, dados técnicos | 0.2 |
| 🟡 **Treinadora Comercial** | Capacitação de equipe, simulação de objeções, didática | 0.6 |

> ⚠️ **Nota:** Estes são exemplos de fábrica. As personas são totalmente configuráveis pelo admin.

---

## ⚙️ Arquitetura do Sistema

```
┌──────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Vercel)                         │
│                     Next.js 16 · React 19 · TS                   │
├──────────┬──────────┬──────────┬──────────┬──────────┬───────────┤
│  💬 Chat │ 📊 Stats │ 📈 Analy │ 📤 Upload│ 📂 Files │ 🧠 Perso  │
│  + Selet │          │  tics    │          │ + Check  │  nas      │
│  or      │          │          │          │  boxes   │  Gallery  │
└─────┬────┴──────────┴──────────┴──────────┴──────────┴───────────┘
      │ HTTPS (streaming SSE)
      ▼
┌──────────────────────────────────────────────────────────────────┐
│                     BACKEND (Cloud Run)                          │
│               FastAPI · Python 3.12 · Uvicorn                    │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  📥 Ingest Pipeline    🔍 RAG Pipeline         🎭 Persona Engine │
│  ┌─────────────────┐   ┌──────────────────┐   ┌────────────────┐ │
│  │ PDF Chunking    │   │ Query Rewrite    │   │ JSON Personas  │ │
│  │ Image Embed     │   │ Intent Classify  │   │ Prompt Builder │ │
│  │ Video Embed     │   │ Pinecone Search  │   │ Temp Control   │ │
│  │ Metadata Tag    │   │ LLM Re-ranking   │   │ Access Filter  │ │
│  │ allowed_personas│   │ Persona Filter   │   │ CRUD Admin     │ │
│  └────────┬────────┘   │ Stream Generate  │   └────────────────┘ │
│           │            └──────────────────┘                      │
│           ▼                     ▼                                │
│  ┌─────────────────────────────────────────────────────┐         │
│  │              Pinecone Serverless                     │         │
│  │  768d vectors · cosine · metadata: allowed_personas  │         │
│  └─────────────────────────────────────────────────────┘         │
│           ▼                                                      │
│  ┌─────────────────────────────────────────────────────┐         │
│  │               Google Gemini API                      │         │
│  │  Embedding 2 Preview · Gemini 2.5 Flash (generate)   │         │
│  └─────────────────────────────────────────────────────┘         │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔒 Controle de Conhecimento

O sistema implementa **filtro de conhecimento por persona** diretamente no Pinecone:

```
Arquivo subiu → metadata: allowed_personas = ["all"]     ← todos acessam (default)
Admin marcou  → metadata: allowed_personas = ["vendedor"] ← só vendedor consulta
```

**Busca no Pinecone:**
```python
filter = {"allowed_personas": {"$in": [persona_id, "all"]}}
```

Resultado: cada especialista vê **apenas os documentos autorizados**, sem afetar os demais.

---

## 🚀 Stack Tecnológica

### Backend
| Tecnologia | Função |
|-----------|---------|
| **FastAPI** | Framework web assíncrono com docs automáticos |
| **Gemini 2.5 Flash** | Modelo de geração (streaming SSE) |
| **Gemini Embedding 2** | Vetorização de documentos (768 dimensões) |
| **Pinecone Serverless** | Banco vetorial com filtros por metadata |
| **PyMuPDF** | Extração de texto e chunks de PDF |
| **Tenacity** | Retry automático para chamadas de API |
| **JWT** | Autenticação admin com tokens |

### Frontend
| Tecnologia | Função |
|-----------|---------|
| **Next.js 16** | Framework React com SSR |
| **React 19** | UI reativa com hooks |
| **TypeScript** | Tipagem estática completa |
| **CSS Light Corporate** | UI corporativa clara com design system limpo |
| **Supabase Auth** | Autenticação de usuários (email/senha + registro) |

### Infraestrutura
| Serviço | Função |
|---------|--------|
| **Google Cloud Run** | Backend serverless (São Paulo) |
| **Vercel** | Frontend com deploy automático |
| **GitHub Actions** | CI/CD com Docker build + push |
| **Pinecone** | Banco vetorial gerenciado |

---

## 📡 Endpoints da API

### Chat & RAG
| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/chat` | Chat RAG completo (pergunta + contexto + persona) |
| `POST` | `/api/chat/stream` | Chat com streaming SSE em tempo real |
| `POST` | `/api/search` | Busca semântica pura (sem geração) |

### Arquivos & Ingestão
| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/upload` | Upload e vetorização de arquivos |
| `GET` | `/api/files` | Inventário Pinecone-first com status e metadata |
| `DELETE` | `/api/files/{name}` | Remove vetores + cria tombstone |
| `PUT` | `/api/files/{name}/personas` | Define quais personas acessam o arquivo |

### Personas (Especialistas)
| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/api/personas` | Lista todas as personas |
| `POST` | `/api/personas` | Cria nova persona |
| `PUT` | `/api/personas/{id}` | Atualiza persona existente |
| `DELETE` | `/api/personas/{id}` | Remove persona |

### Admin & Analytics
| Método | Rota | Descrição |
|--------|------|-----------|
| `POST` | `/api/admin/login` | Autenticação admin (JWT) |
| `GET` | `/api/analytics/stats` | Métricas de uso (período configurável) |
| `GET` | `/api/analytics/top-queries` | Consultas mais frequentes |
| `GET` | `/api/stats` | Estatísticas do Pinecone |

---

## 🛠️ Desenvolvimento Local

### Pré-requisitos
- Python 3.12+
- Node.js 20+
- Conta Pinecone (free tier)
- API Key do Google Gemini

### Backend
```bash
cd backend
pip install -r requirements.txt

# Configure o .env
cp .env.example .env
# Preencha: GEMINI_API_KEY, PINECONE_API_KEY, ADMIN_USER, ADMIN_PASSWORD, JWT_SECRET

uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend
```bash
cd frontend
npm install

# Configure o .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
echo "NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co" >> .env.local
echo "NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ..." >> .env.local

npm run dev
```

---

## 🔐 Variáveis de Ambiente

### Backend (`.env`)
| Variável | Descrição |
|----------|-----------|
| `GEMINI_API_KEY` | Chave da API Google Gemini |
| `PINECONE_API_KEY` | Chave da API Pinecone |
| `PINECONE_INDEX_NAME` | Nome do índice Pinecone |
| `ALLOWED_ORIGINS` | Origens CORS (separadas por vírgula) |
| `ADMIN_USER` | Usuário admin do painel |
| `ADMIN_PASSWORD` | Senha admin do painel |
| `JWT_SECRET` | Segredo para tokens JWT |
| `EMBEDDING_MODEL` | Modelo de embedding (`gemini-embedding-2-preview`) |
| `GENERATION_MODEL` | Modelo de geração (`gemini-2.5-flash`) |

### Frontend (`.env.local`)
| Variável | Descrição |
|----------|-----------|
| `NEXT_PUBLIC_API_URL` | URL do backend |
| `NEXT_PUBLIC_SUPABASE_URL` | URL do projeto Supabase |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Chave pública anon do Supabase |

---

## 📦 Deploy

### Backend (Google Cloud Run)
O deploy é **automatizado via GitHub Actions**. A cada push na branch `main` com mudanças em `backend/`:

1. **Build** → Docker image com Python 3.12-slim
2. **Push** → Artifact Registry (southamerica-east1)
3. **Deploy** → Cloud Run (0-3 instâncias, 512MB, 1 vCPU)

### Frontend (Vercel)
Deploy automático via integração GitHub → Vercel.

---

## 📐 Estrutura do Projeto

```
RAG_HARD/
├── .github/
│   └── workflows/
│       └── deploy-backend.yml      # CI/CD Cloud Run
├── backend/
│   ├── app/
│   │   ├── config.py               # Settings centralizadas (Pydantic)
│   │   ├── main.py                 # FastAPI app + startup
│   │   ├── middleware/
│   │   │   └── auth.py             # JWT admin auth
│   │   ├── routers/
│   │   │   ├── admin_auth.py       # Login admin
│   │   │   ├── analytics.py        # Métricas de uso
│   │   │   ├── chat.py             # Endpoints de chat
│   │   │   ├── files.py            # Gestão de arquivos + personas
│   │   │   └── personas.py         # CRUD especialistas virtuais
│   │   ├── schemas/
│   │   │   ├── models.py           # Schemas de request/response
│   │   │   └── persona.py          # Validação de personas
│   │   └── services/
│   │       ├── analytics.py        # Logging de eventos
│   │       ├── chat_service.py     # Pipeline RAG completo
│   │       ├── embeddings.py       # Gemini Embedding client
│   │       ├── ingest.py           # Chunking + vetorização
│   │       ├── persona_service.py  # CRUD personas (JSON)
│   │       └── pinecone_db.py      # Pinecone client + filtros
│   ├── data/
│   │   └── personas.json           # Configuração das personas
│   ├── Dockerfile
│   └── requirements.txt
└── frontend/
    └── src/
        ├── app/
           ├── globals.css          # Design system (light corporate)
        ├── login/
        │   └── page.tsx         # Página de login
        └── page.tsx             # Roteamento principal
    ├── components/
    │   ├── AuthProvider.tsx  # Supabase auth context
    │   ├── LoginScreen.tsx  # Login/cadastro/reset
    │   ├── ChatView.tsx     # Chat + seletor de persona
    │   ├── FilesView.tsx    # Gestão de arquivos + checkboxes 🧠
    │   ├── PersonasView.tsx # Galeria + editor de especialistas
    │   ├── AnalyticsView.tsx # Dashboard de métricas
    │   ├── UploadView.tsx   # Upload com drag & drop
    │   └── Sidebar.tsx      # Navegação com roles
    ├── lib/
    │   ├── api.ts           # API client tipado
    │   ├── supabase-browser.ts # Supabase client (browser)
    │   └── supabase-server.ts  # Supabase client (server)
    └── types/
        └── index.ts         # TypeScript interfaces
```

---

## 🧪 Pipeline RAG em Detalhe

```
Pergunta do usuário
      │
      ▼
  1. Query Rewrite ──── LLM reescreve para busca semântica
      │
      ▼
  2. Intent Classify ── Classifica intent (técnica, comercial, geral)
      │                  + Ajusta top_k dinamicamente
      ▼
  3. Pinecone Search ── Busca vetorial com filtro de persona
      │                  filter: {allowed_personas: {$in: [id, "all"]}}
      ▼
  4. LLM Re-ranking ── Re-ordena chunks por relevância (1-5)
      │
      ▼
  5. Context Build ──── Monta contexto rico com metadados
      │
      ▼
  6. Stream Generate ── Gemini 2.5 Flash com persona prompt
      │                  + temperatura personalizada
      ▼
  Resposta em streaming (SSE)
```

---

## 👤 Autor

<table>
  <tr>
    <td align="center">
      <strong>Maylton Tavares</strong><br/>
      Arquitetura de IA · Full-Stack · Cloud<br/>
      <em>Engenharia de Soluções com IA Generativa</em>
    </td>
  </tr>
</table>

---

<p align="center">
  <sub>© 2026 Maylton Tavares. Todos os direitos reservados.</sub>
</p>
