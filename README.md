# RAG Hard CMP — Chat Inteligente

Sistema de chat RAG (Retrieval-Augmented Generation) para documentos da Hard CMP, utilizando Gemini 2.5 Flash e Pinecone Vector DB.

## Arquitetura

```
frontend/   → Next.js 16 + TypeScript (deploy: Vercel)
backend/    → FastAPI + Python 3.12 (deploy: Cloud Run)
```

### Stack
- **IA**: Google Gemini 2.5 Flash (geração) + Gemini Embedding 2 (vetorização)
- **Banco Vetorial**: Pinecone Serverless
- **Frontend**: Next.js 16, React 19, TypeScript
- **Backend**: FastAPI, Pydantic, Uvicorn
- **CI/CD**: GitHub Actions → Vercel + Cloud Run

## Desenvolvimento Local

### Backend
```bash
cd backend
pip install -r requirements.txt
# Configure o .env com suas chaves
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Frontend
```bash
cd frontend
npm install
# Configure o .env.local com NEXT_PUBLIC_API_URL=http://localhost:8080
npm run dev
```

## Endpoints da API

| Metodo | Rota | Descricao |
|--------|------|-----------|
| GET | `/api/health` | Health check |
| POST | `/api/chat` | Chat RAG (pergunta + contexto) |
| POST | `/api/search` | Busca semantica |
| POST | `/api/upload` | Upload e ingestao de arquivos |
| GET | `/api/files` | Lista arquivos indexados |
| GET | `/api/stats` | Estatisticas do Pinecone |
| GET | `/docs` | Swagger UI (auto-gerado) |

## Variaveis de Ambiente

### Backend (.env)
- `GEMINI_API_KEY` — Chave da API Google Gemini
- `PINECONE_API_KEY` — Chave da API Pinecone
- `ALLOWED_ORIGINS` — Origens CORS permitidas

### Frontend (.env.local)
- `NEXT_PUBLIC_API_URL` — URL do backend
