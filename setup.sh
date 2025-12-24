#!/bin/bash

# UPC World Bot setup script for Linux/Mac

set -e

echo "🚀 UPC World Bot Setup"
echo "======================"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate
echo "✓ Virtual environment activated"

# Install dependencies
echo "Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"

# Setup .env
if [ ! -f ".env" ]; then
    echo "Creating .env from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your settings"
fi

# Create logs directory
mkdir -p logs
echo "✓ Logs directory created"

# Check Docker (optional)
if command -v docker &> /dev/null; then
    echo "✓ Docker found: $(docker --version)"
else
    echo "⚠️  Docker not found (optional but recommended)"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your settings"
echo "2. Run database migrations: python -m alembic upgrade head"
echo "3. Start the bot: python -m bot.main"
echo ""
