# Werewolf AI - AI-Powered Werewolf Game

<p align="center">
  <strong>An innovative online Werewolf game powered by AI</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.104+-green.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-18.3+-61DAFB.svg" alt="React">
  <img src="https://img.shields.io/badge/TypeScript-5.0+-3178C6.svg" alt="TypeScript">
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
</p>

---

## Overview

Werewolf AI is an innovative online Werewolf (Mafia) game that supports **mixed gameplay between human players and AI players**. The AI players are powered by Large Language Models (LLMs), capable of logical reasoning, strategic decision-making, and natural language interaction, providing an immersive gaming experience.

### Key Features

- **AI-Driven NPCs** - Supports multiple LLM providers including OpenAI, DeepSeek, Gemini, and Anthropic
- **Real-time Gameplay** - WebSocket-based real-time game state synchronization
- **Internationalization** - Bilingual interface (Chinese/English)
- **Secure Authentication** - JWT + OAuth2 (supports GitHub, Google, etc.)
- **Game Analytics** - AI-assisted game analysis and replay
- **Containerized Deployment** - Complete Docker Compose configuration

## Tech Stack

### Backend
| Technology | Purpose |
|------------|---------|
| FastAPI 0.104+ | Web Framework |
| SQLAlchemy 2.0+ | ORM |
| SQLite / PostgreSQL | Database |
| Alembic | Database Migrations |
| JWT + OAuth2 | Authentication |
| OpenAI API | AI Model Integration |

### Frontend
| Technology | Purpose |
|------------|---------|
| React 18.3+ | UI Framework |
| TypeScript 5.0+ | Type Safety |
| Vite 5.0+ | Build Tool |
| TailwindCSS | Styling |
| shadcn/ui | Component Library |
| React Query | State Management |
| i18next | Internationalization |

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Docker & Docker Compose (optional)

### Option 1: Docker Deployment (Recommended)

```bash
# 1. Clone the repository
git clone https://github.com/your-username/werewolf.git
cd werewolf

# 2. Configure environment variables
cp .env.example .env
# Edit .env file with your configuration (e.g., OPENAI_API_KEY)

# 3. Start services
docker-compose up -d

# 4. Access the application
# Frontend: http://localhost:8081
# Backend API: http://localhost:8082
# API Docs: http://localhost:8082/docs
```

### Option 2: Local Development

#### Start Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp ../.env.example ../.env
# Edit .env file

# Initialize database
python -m app.init_db

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Start Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Project Structure

```
werewolf/
├── backend/                 # Backend service
│   ├── app/
│   │   ├── api/            # API routes
│   │   ├── core/           # Core configuration
│   │   ├── models/         # Database models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── i18n/           # Internationalization
│   ├── migrations/         # Database migrations
│   ├── scripts/            # Utility scripts
│   └── requirements.txt
│
├── frontend/               # Frontend application
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── pages/         # Page components
│   │   ├── hooks/         # Custom hooks
│   │   └── lib/           # Utilities
│   └── package.json
│
├── docker-compose.yml      # Docker orchestration
└── README.md
```

## Configuration

### Required Settings

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API Key | `sk-xxx` |
| `JWT_SECRET_KEY` | JWT Signing Key | Random string |

### Optional Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_BASE_URL` | API Base URL | OpenAI official |
| `LLM_MODEL` | Model to use | `gpt-4o-mini` |
| `DEBUG` | Debug mode | `false` |
| `LOG_LEVEL` | Log level | `INFO` |

### Multi-Provider Configuration

The project supports multiple LLM providers, configurable in `.env`:

- **OpenAI** - Default provider
- **DeepSeek** - Cost-effective Chinese provider
- **Gemini** - Google's AI service
- **Anthropic** - Claude models

## Game Rules

### Roles

| Role | Team | Ability |
|------|------|---------|
| Werewolf | Werewolf | Can kill one player each night |
| Villager | Good | No special ability, votes to find werewolves |
| Seer | Good | Can check one player's identity each night |
| Witch | Good | Has one healing potion and one poison |
| Hunter | Good | Can shoot one player upon death |

### Game Flow

1. **Role Assignment** - System randomly assigns roles to all players
2. **Night Phase** - Werewolves kill, special roles take actions
3. **Day Phase** - Players discuss and vote to exile suspects
4. **Victory Condition** - Game ends when all werewolves are eliminated or good players are outnumbered

## API Documentation

After starting the backend service, access the API documentation at:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm run test
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## License

This project is licensed under the [MIT License](LICENSE).

## Contact

- Issues: [GitHub Issues](https://github.com/your-username/werewolf/issues)
- Wiki: [Project Documentation](https://github.com/your-username/werewolf/wiki)

---

<p align="center">
  Made with love by Werewolf AI Team
</p>
