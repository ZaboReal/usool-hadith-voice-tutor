#!/bin/bash

# Usool al-Hadith Voice Agent - Frontend Setup Script

echo "🕌 Setting up Usool al-Hadith Voice Agent Frontend..."

# Check Node version
echo "📋 Checking Node.js version..."
node_version=$(node --version)
echo "Found Node.js $node_version"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Check for .env file
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env with your LiveKit URL before continuing."
else
    echo "✅ .env file found"
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your LiveKit URL"
echo "2. Make sure backend is running"
echo "3. Run: npm run dev"
echo "4. Open http://localhost:3000 in your browser"
echo ""
