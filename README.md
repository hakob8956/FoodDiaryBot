# FoodGPT - AI Nutrition Tracking Telegram Bot

A Telegram bot that helps you track your nutrition effortlessly using AI-powered food analysis. Simply send a photo of your meal or describe what you ate, and get instant calorie and macro estimates.

## Features

- **AI Food Analysis** - Send a photo or text description to log meals with automatic calorie/macro estimation
- **Personalized Calorie Targets** - Calculates daily needs using Mifflin-St Jeor formula based on your profile
- **Progress Tracking** - See daily totals and remaining calories after each meal
- **Nutrition Summaries** - Get detailed reports for any date or date range
- **Smart Insights** - Personalized feedback on eating habits and suggestions for improvement
- **Easy Management** - Delete entries, update weight, override calorie targets
- **Mini App Dashboard** - Interactive calendar, charts, and detailed meal history via Telegram WebApp
- **Daily Reminders** - Configurable notifications if you haven't logged food
- **Cloud Database Support** - Optional Turso integration for cloud deployment

## Tech Stack

**Backend:**
- **Python 3.9+** with asyncio
- **python-telegram-bot** - Telegram Bot API wrapper
- **OpenAI GPT-4o** - Vision API for food image analysis
- **FastAPI** - Mini App API server
- **SQLite / Turso** - Local or cloud database
- **Pydantic** - Data validation and settings management

**Frontend (Mini App):**
- **React 18** + **Vite**
- **Recharts** - Charts and visualizations
- **Telegram WebApp SDK** - Native Telegram integration

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/FoodDiaryTelegram.git
cd FoodDiaryTelegram
```

### 2. Create virtual environment

```bash
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
OPENAI_API_KEY=your_openai_api_key
```

**Getting your tokens:**
- **Telegram Bot Token**: Message [@BotFather](https://t.me/BotFather) on Telegram, use `/newbot` command
- **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)

### 5. Run the bot

```bash
python main.py
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Set up your profile (weight, height, age, sex, activity level, goal) |
| `/profile` | View your current stats and calorie target |
| `/setcalories <number>` | Override your daily calorie target (e.g., `/setcalories 2200`) |
| `/setweight <number>` | Update your weight in kg (e.g., `/setweight 75`) |
| `/summarize [date]` | Get nutrition summary (today, yesterday, this week, or specific date) |
| `/delete [id]` | Delete a food entry |
| `/notifications` | Configure daily reminder settings |
| `/rawlog` | Export all logs as JSON |
| `/help` | Show all commands |

## Usage

### Logging Food

Simply send the bot:
- A **photo** of your meal
- A **text description** (e.g., "grilled chicken with rice and vegetables")
- A **photo with caption** for best accuracy

The bot will respond with:
```
Logged: Grilled chicken, brown rice, steamed broccoli
~520 kcal | 45g protein

Today: 1,240/2,000 kcal (760 remaining)

(Entry #42 - use /delete 42 to remove)
```

### Getting Summaries

```
/summarize              # Today's summary
/summarize yesterday    # Yesterday's summary
/summarize this week    # This week's summary
/summarize 2024-11-15   # Specific date
/summarize 2024-11-10 to 2024-11-20  # Date range
```

## Project Structure

```
FoodDiaryTelegram/
├── main.py                 # Application entry point (bot + API server)
├── config.py               # Environment configuration
├── requirements.txt        # Python dependencies
├── bot/
│   ├── handlers/           # Command handlers
│   │   ├── start.py        # Onboarding flow
│   │   ├── profile.py      # Profile commands
│   │   ├── food_log.py     # Food logging
│   │   ├── summary.py      # Nutrition summaries
│   │   ├── delete.py       # Delete entries
│   │   ├── notifications.py # Reminder settings
│   │   └── help.py         # Help command
│   └── keyboards/          # Inline keyboards
├── database/
│   ├── connection.py       # SQLite/Turso dual connection
│   ├── models.py           # Pydantic models
│   ├── migrations.py       # Schema setup
│   └── repositories/       # Data access layer
├── services/
│   ├── calorie_calculator.py   # BMR/TDEE calculations
│   ├── openai_service.py       # GPT-4o integration
│   ├── food_analyzer.py        # Food analysis
│   ├── summary_generator.py    # Report generation
│   └── reminder_service.py     # Daily reminders
├── webapp/
│   ├── api/                # FastAPI backend
│   │   ├── server.py       # API server setup
│   │   └── routes/         # API endpoints
│   └── frontend/           # React Mini App
│       ├── src/
│       │   ├── components/ # Calendar, Charts, DaySummary
│       │   └── api/        # API client
│       └── package.json
├── utils/                  # Utilities
└── data/                   # SQLite database (created at runtime)
```

## Calorie Calculation

Uses the **Mifflin-St Jeor** equation:
- **Male**: BMR = (10 × weight) + (6.25 × height) - (5 × age) + 5
- **Female**: BMR = (10 × weight) + (6.25 × height) - (5 × age) - 161

Activity multipliers:
- Sedentary: 1.2
- Lightly Active: 1.375
- Moderately Active: 1.55
- Very Active: 1.725

Goal adjustments:
- Lose weight: -500 kcal
- Maintain: 0
- Gain weight: +300 kcal

## Mini App Setup

The Mini App provides a visual dashboard with calendar, charts, and meal history.

### Development

```bash
cd webapp/frontend
npm install
npm run dev
```

### Production

1. Build the frontend:
   ```bash
   cd webapp/frontend
   npm run build
   ```

2. Set `WEBAPP_URL` in `.env` to your public HTTPS URL

3. Configure in BotFather:
   - `/mybots` → Select bot → Bot Settings → Menu Button
   - Set URL to your `WEBAPP_URL`

### Local Testing with ngrok

```bash
ngrok http 8080
# Copy the HTTPS URL to WEBAPP_URL in .env
```

## Cloud Database (Turso)

For deployment without local storage (e.g., Raspberry Pi):

1. Install Turso CLI and create database:
   ```bash
   curl -sSfL https://get.tur.so/install.sh | bash
   turso db create foodgpt
   ```

2. Get credentials:
   ```bash
   turso db show foodgpt --url
   turso db tokens create foodgpt
   ```

3. Update `.env`:
   ```
   USE_TURSO=true
   TURSO_DB_URL=libsql://your-db.turso.io
   TURSO_AUTH_TOKEN=your-token
   ```

## License

MIT License
