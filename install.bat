@echo off
echo 🚀 Installing LangGraph Agent Service (Python)
echo ==============================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

echo ✅ Python detected

REM Check if pip is installed
pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ pip is not installed. Please install pip first.
    pause
    exit /b 1
)

echo ✅ pip detected

REM Create virtual environment
echo 📦 Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️ Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo 📚 Installing dependencies...
pip install -r requirements.txt

REM Create .env file if it doesn't exist
if not exist .env (
    echo 📝 Creating .env file from template...
    copy env_example.txt .env
    echo ⚠️  Please edit .env file with your configuration
) else (
    echo ✅ .env file already exists
)

echo.
echo 🎉 Installation completed!
echo.
echo Next steps:
echo 1. Edit .env file with your configuration
echo 2. Run: venv\Scripts\activate.bat
echo 3. Run: python run.py
echo.
echo For development:
echo - Activate venv: venv\Scripts\activate.bat
echo - Run service: python run.py
echo - Deactivate venv: deactivate
echo.
pause
