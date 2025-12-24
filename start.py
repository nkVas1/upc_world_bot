"""Under People Club Bot Starter Script."""
import os
import sys
import subprocess
import signal
import time
from pathlib import Path
from datetime import datetime


class Color:
    """ANSI color codes."""
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    END = '\033[0m'


class Config:
    """Configuration for starter."""
    PROJECT_ROOT = Path(__file__).parent
    BOT_PID_FILE = PROJECT_ROOT / "bot.pid"
    LOG_FILE = PROJECT_ROOT / "logs" / f"bot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    VENV_PATH = PROJECT_ROOT / "venv"
    PYTHON_EXECUTABLE = VENV_PATH / ("Scripts" if sys.platform == "win32" else "bin") / ("python.exe" if sys.platform == "win32" else "python")


def print_banner():
    """Print beautiful banner."""
    banner = f"""
{Color.CYAN}
╔══════════════════════════════════════════════════════════╗
║  🌑 Under People Club Bot v3.0                          ║
║  Telegram Bot для Under People Club                    ║
║  Modern, Fast & Reliable Bot Framework                 ║
╚══════════════════════════════════════════════════════════╝
{Color.END}
"""
    print(banner)


def print_info(component: str, message: str):
    """Print info message."""
    prefixes = {
        "bot": ("🤖 BOT", Color.GREEN),
        "api": ("🌐 API", Color.BLUE),
        "db": ("🗄️  DB", Color.CYAN),
        "setup": ("⚙️  SETUP", Color.YELLOW),
        "info": ("ℹ️  INFO", Color.CYAN),
    }
    
    prefix_text, color = prefixes.get(component, ("📌 LOG", Color.BLUE))
    print(f"{color}[{prefix_text}]{Color.END} {message}")


def print_success(message: str):
    """Print success message."""
    print(f"{Color.GREEN}✅ {message}{Color.END}")


def print_error(message: str):
    """Print error message."""
    print(f"{Color.RED}❌ {message}{Color.END}")


def print_warning(message: str):
    """Print warning message."""
    print(f"{Color.YELLOW}⚠️  {message}{Color.END}")


def check_env():
    """Check .env file exists."""
    env_file = Config.PROJECT_ROOT / ".env"
    if not env_file.exists():
        print_error(".env файл не найден!")
        print_info("info", "Создайте .env на основе .env.example")
        print_info("info", "Команда: cp .env.example .env")
        sys.exit(1)
    
    print_success(".env файл найден")


def check_dependencies():
    """Check Python dependencies."""
    try:
        import telegram
        print_success("python-telegram-bot установлен")
    except ImportError:
        print_error("python-telegram-bot не установлен!")
        print_info("info", "Выполните: pip install -r requirements.txt")
        sys.exit(1)


def check_directories():
    """Check and create necessary directories."""
    directories = [
        Config.PROJECT_ROOT / "logs",
        Config.PROJECT_ROOT / "bot" / "__pycache__",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
    
    print_success("Директории проверены")


def start_bot():
    """Start the bot."""
    print_info("setup", "Запускаю бота...")
    
    try:
        # Create logs directory
        Config.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        # Start bot process
        cmd = [str(Config.PYTHON_EXECUTABLE), "-m", "bot.main"]
        
        with open(Config.LOG_FILE, "w", encoding="utf-8") as log_file:
            process = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                cwd=str(Config.PROJECT_ROOT),
            )
            
            # Save PID
            with open(Config.BOT_PID_FILE, "w") as pid_file:
                pid_file.write(str(process.pid))
            
            print_success(f"Бот запущен (PID: {process.pid})")
            print_info("info", f"Логи: {Config.LOG_FILE}")
            
            # Print startup info
            print()
            print_info("bot", "🤖 Telegram Bot работает")
            print_info("bot", "   Отправьте /start в боте для начала")
            print()
            print_info("info", "=" * 60)
            print_warning("Нажмите Ctrl+C для остановки бота")
            print_info("info", "=" * 60)
            print()
            
            # Wait for process
            process.wait()
            
    except Exception as e:
        print_error(f"Ошибка запуска бота: {e}")
        sys.exit(1)


def stop_bot():
    """Stop the bot."""
    pid_file = Config.BOT_PID_FILE
    
    if not pid_file.exists():
        print_error("PID файл не найден")
        return
    
    try:
        with open(pid_file, "r") as f:
            pid = int(f.read().strip())
        
        os.kill(pid, signal.SIGTERM)
        print_success(f"Бот остановлен (PID: {pid})")
        pid_file.unlink()
        
    except (ProcessLookupError, ValueError) as e:
        print_error(f"Ошибка остановки: {e}")


def setup_venv():
    """Setup virtual environment."""
    if Config.VENV_PATH.exists():
        print_success("Виртуальная среда уже существует")
        return
    
    print_info("setup", "Создаю виртуальную среду...")
    
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(Config.VENV_PATH)],
            check=True
        )
        print_success("Виртуальная среда создана")
        
        # Install requirements
        print_info("setup", "Устанавливаю зависимости...")
        subprocess.run(
            [str(Config.PYTHON_EXECUTABLE), "-m", "pip", "install", "-r", "requirements.txt"],
            cwd=str(Config.PROJECT_ROOT),
            check=True
        )
        print_success("Зависимости установлены")
        
    except subprocess.CalledProcessError as e:
        print_error(f"Ошибка установки: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    print_banner()
    
    # Check if running from correct directory
    if not (Config.PROJECT_ROOT / "bot" / "main.py").exists():
        print_error("Запустите скрипт из корневой директории проекта")
        sys.exit(1)
    
    # Perform checks
    print_info("setup", "Выполняю проверки...")
    check_env()
    check_directories()
    setup_venv()
    check_dependencies()
    
    print()
    print_success("Все проверки пройдены!")
    print()
    
    # Start bot
    start_bot()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print_warning("Получен сигнал прерывания")
        print_info("info", "Остановка бота...")
        sys.exit(0)
