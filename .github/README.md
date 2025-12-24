# Under People Club World Bot v3.0

Modern Telegram bot for Under People Club youth community.

## Features

- 🎟️ **Event Ticket System** - Buy tickets for events with flexible payment
- 💰 **UP Coins Economy** - Internal currency with website integration
- 🔗 **Referral Program** - Multi-tier rewards system
- 👤 **User Profiles** - Personal cabinet with QR codes and statistics
- 📊 **Admin Panel** - Management tools and analytics
- 🎮 **Games & Achievements** - Engagement and reward system
- 🔐 **Secure & Modern** - Production-ready with proper error handling

## Quick Start

### Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/underpeople/upc-world-bot.git
cd upc-world-bot

# Copy environment
cp .env.example .env

# Edit .env with your settings
nano .env

# Run
docker-compose up -d

# Check logs
docker-compose logs -f bot
```

### Manual Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
nano .env

# Run migrations
python -m alembic upgrade head

# Start bot
python -m bot.main
```

## Commands

- `/start` - Start using bot
- `/profile` - User profile & statistics
- `/referral` - Referral program
- `/daily` - Claim daily bonus
- `/help` - Help & support

## Admin Commands

- `/admin` - Admin panel
- `/userinfo <user_id>` - User information
- `/addcoins <user_id> <amount>` - Add coins to user
- `/broadcast <message>` - Broadcast message

## Architecture

```
bot/
├── config.py           # Configuration
├── main.py            # Entry point
├── database/          # Database layer
├── handlers/          # Message handlers
├── services/          # Business logic
├── middlewares/       # Request processing
├── keyboards/         # UI buttons
└── utils/            # Utilities
```

## Environment Variables

See `.env.example` for all required variables:

- `BOT_TOKEN` - Telegram Bot API token
- `DATABASE_URL` - PostgreSQL connection
- `REDIS_URL` - Redis connection
- `ADMIN_IDS` - Comma-separated admin user IDs
- `SECRET_KEY` - Application secret
- And more...

## Documentation

- [README.md](README.md) - Full documentation
- [DEVELOPMENT.md](DEVELOPMENT.md) - Developer guide
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines

## Project Status

- ✅ Core bot functionality
- ✅ Database models & repositories
- ✅ User authentication & authorization
- ✅ Ticket shop system
- ✅ Referral program
- ✅ Admin panel
- ✅ Docker containerization
- 🚀 Ready for production

## License

Proprietary - Under People Club

## Support

- 📧 Email: tech@underpeople.club
- 🔗 Telegram: [@underpeople_club](https://t.me/underpeople_club)
- 🌐 Website: [underpeople.club](https://underpeople.club)

## Contributors

Built with ❤️ by Under People Club Tech Team
