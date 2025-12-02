# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FoodGPT is a Telegram bot for AI-powered nutrition tracking. Users send food photos or text descriptions, and GPT-4o Vision analyzes them to estimate calories and macros.

## Commands

### Run the Bot
```bash
python main.py
```
This starts both the Telegram bot and the Mini App API server (FastAPI on port 8080).

### Frontend Development (Mini App)
```bash
cd webapp/frontend
npm install
npm run dev      # Development server
npm run build    # Production build
```

### Dependencies
```bash
pip install -r requirements.txt
```

## Architecture

### Two Services in One Process
`main.py` runs both services:
1. **Telegram Bot** - Main thread, uses python-telegram-bot for polling
2. **Mini App API** - Background thread, FastAPI/Uvicorn server for the Telegram WebApp

### Database Layer
- **Dual support**: SQLite (local, default) or Turso (cloud)
- Toggle with `USE_TURSO=true` in `.env`
- `database/connection.py` - Singleton `db` handles both backends transparently
- `database/repositories/` - Data access layer (user_repo, food_log_repo)

### Bot Handler Pattern
Handlers in `bot/handlers/` export a `get_*_handler()` function returning a telegram handler. Order matters in `main.py`:
1. ConversationHandler for `/start` onboarding (must be first)
2. Command handlers
3. `food_log` handler last (catches all photos/text not handled above)

### Mini App (webapp/)
- **Backend**: `webapp/api/` - FastAPI routes with Telegram initData authentication
- **Frontend**: `webapp/frontend/` - React + Vite + Recharts
- Auth flow: Frontend sends `X-Telegram-Init-Data` header, validated via HMAC with bot token

### OpenAI Integration
`services/openai_service.py` handles GPT-4o Vision calls with retry logic (tenacity). System prompt in `services/food_analyzer.py` returns structured JSON with food items, calories, and macros.

## Key Files

- `config.py` - Pydantic settings from environment variables
- `database/migrations.py` - Schema creation, runs on startup
- `services/calorie_calculator.py` - Mifflin-St Jeor BMR/TDEE formula
- `webapp/api/routes/auth.py` - Telegram WebApp authentication

## Environment Variables

Required in `.env`:
- `TELEGRAM_BOT_TOKEN` - From @BotFather
- `OPENAI_API_KEY` - For GPT-4o Vision

Optional:
- `WEBAPP_URL` - Public URL for Mini App (ngrok for dev)
- `USE_TURSO`, `TURSO_DB_URL`, `TURSO_AUTH_TOKEN` - Cloud database
- `GROWTHBOOK_CLIENT_KEY` - Feature flags
