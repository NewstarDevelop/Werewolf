# 🐺 Werewolf

[English](./README.en.md) | [简体中文](./README.md)

An AI-powered online Werewolf (Mafia) game supporting human and AI players. Built with FastAPI + React + Docker, providing a smooth gaming experience with intelligent AI opponents.

**Live Demo**: https://werewolf.newstardev.de (Mock mode, no real API key configured)

![Game](https://img.shields.io/badge/Game-Werewolf-red)
![Python](https://img.shields.io/badge/Python-3.13-blue)
![React](https://img.shields.io/badge/React-18.3-61dafb)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ed)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

### Core Gameplay
- **Complete Game Flow**: Supports Werewolf, Seer, Witch, Hunter, Guard, Wolf King, White Wolf King roles
- **AI Players**: Intelligent AI powered by OpenAI GPT with mock mode support
- **Multi-Room System**: Multiple concurrent games with room creation and joining
- **Mixed Mode**: Support for pure human, pure AI, or human+AI hybrid games
- **Real-time Chat**: In-game chat system with message logging
- **AI Game Analysis**: View AI-generated game analysis after matches

### User System
- **User Registration & Login**: Email and password authentication
- **OAuth Authentication**: Support for linux.do OAuth2 third-party login
- **JWT Authentication**: Secure token-based auth with HttpOnly Cookies
- **User Profile**: Avatar, nickname, and bio management

### Technical Features
- **Modern UI**: Beautiful interface built with shadcn/ui, pure black theme
- **Docker Ready**: One-click deployment, out-of-the-box
- **Responsive Design**: Desktop and mobile support
- **Data Persistence**: SQLite database for user and room storage
- **Multi-language**: Switch between English and Chinese

---

## 🎭 Game Roles

### Classic 9-Player Mode
| Role | Faction | Ability |
|------|---------|---------|
| 🐺 Werewolf (×3) | Werewolf | Can eliminate a player each night |
| 👁️ Seer | Village | Can inspect a player's identity each night |
| 🧪 Witch | Village | Has one healing potion and one poison; cannot use poison on the same night after using healing |
| 🔫 Hunter | Village | Can shoot a player when eliminated (except when poisoned) |
| 👨‍🌾 Villager (×3) | Village | No special abilities |

### Extended 12-Player Mode
| Role | Faction | Ability |
|------|---------|---------|
| 🛡️ Guard | Village | Can protect a player from werewolf attack each night |
| 👑 Wolf King | Werewolf | Can take down a player when eliminated |
| ⚪ White Wolf King | Werewolf | Can self-destruct during the day to take down a player |

---

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- (Optional) OpenAI API Key for real AI opponents
- (Optional) linux.do OAuth credentials for third-party login

### Start with Docker

```bash
# Clone repository
git clone https://github.com/NewstarDevelop/Werewolf.git
cd Werewolf

# Copy environment template
cp .env.example .env

# Edit configuration (fill in API keys, etc.)
nano .env

# Start services
docker compose up
```

**Access the Game**
- 🎮 Frontend: http://localhost:8081
- 📡 Backend API: http://localhost:8082
- 📚 API Documentation: http://localhost:8082/docs

### Local Development

#### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

---

## 🎮 Gameplay

### Game Modes

#### Mixed Mode (Human + AI)
1. Create a room and wait for players to join
2. Room owner clicks "Fill AI and Start"
3. System automatically fills remaining seats with AI
4. Example: 3 humans + 6 AI

### Game Flow

1. **Start Game**: Create or join a game through the room system
2. **Role Assignment**: System automatically assigns roles
3. **Night Phase**:
   - Guard chooses protection target
   - Werewolves discuss and choose kill target
   - Seer inspects a player's identity
   - Witch first decides healing, then poison
4. **Day Phase**:
   - Announce night deaths
   - Last words from dead players
   - All players speak in turn
   - Vote to eliminate a suspicious player
5. **Victory Conditions**:
   - Village wins: Eliminate all werewolves
   - Werewolves win: Wolf count ≥ villager count, or all villagers dead, or all special roles dead

### Controls

- **Speaking**: During day phase, enter your message and click "Confirm"
- **Voting**: During voting phase, click on a player's avatar to vote
- **Using Abilities**: During night phase, click "Skill" button to use your role's ability

---

## 📁 Project Structure

```
Werewolf/
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── api/                # API routes
│   │   │   ├── dependencies.py # Dependency injection
│   │   │   └── endpoints/
│   │   │       ├── auth.py     # Authentication API
│   │   │       ├── game.py     # Game API
│   │   │       ├── room.py     # Room API
│   │   │       └── users.py    # User API
│   │   ├── core/               # Core configuration
│   │   │   ├── config.py       # Configuration management
│   │   │   ├── database.py     # Database config
│   │   │   └── security.py     # Security utilities
│   │   ├── i18n/               # Internationalization
│   │   │   ├── en.json         # English translations
│   │   │   └── zh.json         # Chinese translations
│   │   ├── models/             # Data models
│   │   │   ├── game.py         # Game model
│   │   │   ├── room.py         # Room model
│   │   │   └── user.py         # User model
│   │   ├── schemas/            # Pydantic schemas
│   │   │   ├── auth.py         # Auth schemas
│   │   │   ├── enums.py        # Enum definitions
│   │   │   └── game.py         # Game schemas
│   │   └── services/           # Business logic
│   │       ├── game_engine.py  # Game engine
│   │       ├── game_analyzer.py# Game analysis
│   │       ├── llm.py          # AI service
│   │       ├── oauth.py        # OAuth service
│   │       ├── prompts.py      # AI prompts
│   │       └── room_manager.py # Room management
│   ├── data/                   # Data storage
│   ├── migrations/             # Database migrations
│   ├── tests/                  # Test files
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # React components
│   │   │   ├── game/          # Game components
│   │   │   │   ├── ChatLog.tsx
│   │   │   │   ├── DebugPanel.tsx
│   │   │   │   ├── GameActions.tsx
│   │   │   │   ├── GameAnalysisDialog.tsx
│   │   │   │   ├── GameStatusBar.tsx
│   │   │   │   ├── PlayerCard.tsx
│   │   │   │   └── PlayerGrid.tsx
│   │   │   └── ui/            # UI components
│   │   ├── hooks/             # Custom hooks
│   │   ├── pages/             # Page components
│   │   │   ├── auth/          # Auth pages
│   │   │   │   ├── LoginPage.tsx
│   │   │   │   ├── RegisterPage.tsx
│   │   │   │   └── OAuthCallback.tsx
│   │   │   ├── GamePage.tsx   # Game page
│   │   │   ├── ProfilePage.tsx# Profile page
│   │   │   ├── RoomLobby.tsx  # Room lobby
│   │   │   └── RoomWaiting.tsx# Room waiting
│   │   ├── services/          # API services
│   │   │   ├── api.ts         # Game API
│   │   │   ├── authService.ts # Auth service
│   │   │   └── roomApi.ts     # Room API
│   │   └── utils/             # Utilities
│   ├── public/
│   │   └── locales/           # Translation files (zh/en)
│   ├── Dockerfile
│   ├── nginx.conf
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## 🛠️ Tech Stack

### Backend
- **FastAPI**: Modern Python web framework
- **SQLAlchemy**: ORM database operations
- **Pydantic**: Data validation and serialization
- **OpenAI API**: AI decision-making engine
- **JWT + HttpOnly Cookie**: Secure authentication
- **Uvicorn**: ASGI server

### Frontend
- **React 18**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool
- **TanStack Query**: Data fetching and state management
- **shadcn/ui**: UI component library
- **Tailwind CSS**: Styling framework
- **React Router**: Routing
- **i18next**: Internationalization
- **Recharts**: Charts component

### Infrastructure
- **Docker & Docker Compose**: Containerized deployment
- **Nginx**: Static file serving
- **SQLite**: Data persistence

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Application Configuration
DEBUG=false
DEBUG_MODE=false
CORS_ORIGINS=http://localhost:8081,http://127.0.0.1:8081

# JWT Configuration
JWT_SECRET_KEY=your-very-long-random-secret-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth Configuration (linux.do)
LINUXDO_CLIENT_ID=your_client_id
LINUXDO_CLIENT_SECRET=your_client_secret
LINUXDO_REDIRECT_URI=http://localhost:8082/api/auth/callback/linuxdo
```

### Production Security Configuration

```env
# Must specify exact frontend domain, wildcards "*" are prohibited
CORS_ORIGINS=https://your-domain.com

# Use a strong random key (at least 32 characters)
JWT_SECRET_KEY=your-very-long-random-secret-key-here

# Disable debug mode
DEBUG=false
DEBUG_MODE=false
```

⚠️ **Security Warning**: When using HttpOnly Cookie authentication, `CORS_ORIGINS` must be set to specific domains. **Using `*` is prohibited** due to CSRF attack risks.

### Per-Player LLM Configuration

You can configure individual LLM providers for each AI player (seats 2-9):

```env
# Configure LLM for Player 2
AI_PLAYER_2_NAME=player2
AI_PLAYER_2_API_KEY=your_api_key
AI_PLAYER_2_BASE_URL=https://api.openai.com/v1
AI_PLAYER_2_MODEL=gpt-4o-mini
AI_PLAYER_2_TEMPERATURE=0.7
AI_PLAYER_2_MAX_TOKENS=500
AI_PLAYER_2_MAX_RETRIES=2
```

### AI Game Analysis Configuration

```env
# AI Analysis Configuration (optional, defaults to OpenAI config if not set)
ANALYSIS_PROVIDER=openai
ANALYSIS_MODEL=gpt-4o
ANALYSIS_MODE=comprehensive
ANALYSIS_LANGUAGE=auto
ANALYSIS_CACHE_ENABLED=true
ANALYSIS_MAX_TOKENS=4000
ANALYSIS_TEMPERATURE=0.7
```

### Mock Mode

If `OPENAI_API_KEY` is not configured, the system will automatically enter Mock mode, and AI players will use preset random strategies.

### AI Debug Panel

The AI thought process debug panel only displays when `DEBUG_MODE=true` is configured in `.env`.

---

## 📡 API Documentation

After starting the service, visit http://localhost:8082/docs to view the complete API documentation (Swagger UI).

### Main API Endpoints

#### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/oauth/linuxdo` - OAuth login
- `GET /api/auth/callback/linuxdo` - OAuth callback

#### Users
- `GET /api/users/me` - Get current user info
- `PUT /api/users/me` - Update user profile

#### Room Management
- `POST /api/rooms` - Create room
- `GET /api/rooms` - Get room list
- `GET /api/rooms/{room_id}` - Get room details
- `POST /api/rooms/{room_id}/join` - Join room
- `POST /api/rooms/{room_id}/ready` - Toggle ready status
- `POST /api/rooms/{room_id}/start` - Start game
- `DELETE /api/rooms/{room_id}` - Delete room

#### Game Operations
- `GET /api/game/{game_id}/state` - Get game state
- `POST /api/game/{game_id}/action` - Player action
- `POST /api/game/{game_id}/step` - Advance game progress
- `GET /api/game/{game_id}/analysis` - Get game analysis

---

## 🐛 Troubleshooting

### Docker Issues

**Problem: Container fails to start**
```bash
# View logs
docker-compose logs -f

# Restart services
docker-compose restart
```

**Problem: Port in use**
```bash
# Modify port mapping in docker-compose.yml
# For example: change 8081:80 to 8082:80
```

### Frontend Development Issues

**Problem: npm install fails**
```bash
# Clear cache and retry
npm cache clean --force
npm install
```

---

## 📝 Development Progress

### Current Version (v1.4 - 2025-01-01)

#### User System
- ✅ User registration/login (email + password)
- ✅ linux.do OAuth2 third-party login
- ✅ JWT + HttpOnly Cookie authentication
- ✅ Refresh token rotation mechanism
- ✅ User profile management (avatar, nickname, bio)

#### Game Features
- ✅ 12-player extended mode (Guard, Wolf King, White Wolf King)
- ✅ Werewolf self-kill strategy
- ✅ Complete win condition logic
- ✅ AI game analysis with caching

#### Security & Stability
- ✅ Async LLM calls
- ✅ Game state locking to prevent race conditions
- ✅ Input sanitization to prevent prompt injection
- ✅ CSRF protection (OAuth state verification)

### Version History

| Version | Date | Highlights |
|---------|------|------------|
| v1.4 | 2025-01-01 | User system, OAuth login, 12-player mode |
| v1.3 | 2024-12-30 | Security fixes, stability, self-kill |
| v1.2 | 2024-12-30 | Multi-room, AI fill, mixed mode |
| v1.1 | 2024-12-28 | AI game analysis, caching |
| v1.0 | 2024-12-27 | Initial release, i18n support |

### Planned Features
- [ ] WebSocket real-time communication
- [ ] Game replay feature
- [ ] AI strategy optimization
- [ ] Game statistics and leaderboards
- [ ] More game configuration options

---

## 🤝 Contributing

Issues and Pull Requests are welcome!

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

**If this project helps you, please give it a ⭐ Star!**
