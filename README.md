# RECEPTOR CO-PILOT

AI-powered restaurant management copilot with deep iiko integration.

## What is RECEPTOR?

RECEPTOR helps restaurant owners and managers optimize their operations through AI — from menu engineering and tech card generation to sales analytics and competitive intelligence. Natively integrated with iiko POS (Cloud API + RMS Server).

### Key Features

- **AI Chat** — Conversational interface for all restaurant operations. Ask about revenue, search products, get recommendations
- **iiko Integration** — Dual support: iikoCloud API + iiko RMS Server. Sync nomenclature, pull sales reports, manage organizations
- **BI Dashboard** — Revenue analytics, top dishes, category breakdowns, shift reports. CSV export
- **Deep Research** — Automated competitive analysis with SWOT, competitor benchmarking, market positioning
- **Venue Profile** — Restaurant context that personalizes all AI responses

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, PyMongo |
| Frontend | React 18, Tailwind CSS, Recharts |
| Database | MongoDB |
| AI/LLM | OpenAI, OpenRouter (multi-model routing) |
| Search | Tavily (web), RAG (knowledge base) |
| iiko | pyiikocloudapi, REST API |
| Deploy | Vercel (frontend), Render (backend) |

## Quick Start

### Backend

```bash
cd backend
cp .env.example .env  # Fill in your values
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
cp .env.example .env.local  # Set REACT_APP_API_URL
npm install
npm start
```

### Environment Variables

See `backend/.env.example` and `frontend/.env.example` for all required configuration.

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes (chat, iiko, venue, history)
│   │   ├── core/         # Config, database, encryption
│   │   └── services/     # Business logic (iiko, LLM, RAG, research)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── config.js     # Centralized configuration
│   │   └── App.js        # Main application
│   └── package.json
├── docs/archive/         # Historical documentation
├── tests/legacy/         # Test scripts archive
└── render.yaml           # Render deployment config
```

## License

Proprietary. All rights reserved.
