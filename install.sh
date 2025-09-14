#!/bin/bash

echo "🚀 Installing LangGraph Agent Service (Python)"
echo "=============================================="

# Check if Python 3.8+ is installed
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "✅ Python $python_version detected"
else
    echo "❌ Python 3.8+ is required. Current version: $python_version"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip3 first."
    exit 1
fi

echo "✅ pip3 detected"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env_example.txt .env
    echo "⚠️  Please edit .env file with your configuration"
else
    echo "✅ .env file already exists"
fi

# Make run.py executable
chmod +x run.py

echo ""
echo "🎉 Installation completed!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python run.py"
echo ""
echo "For development:"
echo "- Activate venv: source venv/bin/activate"
echo "- Run service: python run.py"
echo "- Deactivate venv: deactivate"
