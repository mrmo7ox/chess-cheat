# Chess Bot - Automated Chess.com Assistant

Ever wanted a chess companion that plays for you? This Python-based chess bot automates your gameplay on Chess.com by leveraging the powerful Stockfish chess engine. Simply set your account credentials, adjust the engine strength, and let it handle the moves while you watch from a clean, modern desktop interface.

## Features

- **Automated Gameplay** - Automatically plays chess on Chess.com so you don't have to
- **Stockfish Integration** - Powered by the Stockfish chess engine for intelligent move analysis
- **Desktop UI** - Clean, modern web-based interface that's easy to control
- **Adjustable Strength** - Change the engine's search depth in real-time to adjust difficulty
- **Multi-Account Support** - Manage multiple Chess.com accounts effortlessly
- **Session Management** - Your progress is saved automatically between sessions
- **Standalone App** - Package everything into a single executable file

## Project Structure

Here's how the code is organized:

```
├── main.py              # The main entry point—starts Flask and the UI
├── chess_bot.py         # Core logic for browser control and move execution
├── config.json          # Your settings and preferences
├── session.json         # Automatically saved session data
├── acc.json            # Your Chess.com login info (keep this private!)
├── Makefile            # Shortcuts for common tasks
├── cheat.spec          # Configuration for building the executable
└── web/                # The user interface
    ├── index.html      # Main HTML page
    ├── app.js          # JavaScript logic
    └── style.css       # Styling
```

## What You'll Need

Before you get started, make sure you have:

- Python 3.x installed on your system
- Chrome or Chromium browser
- An internet connection (the bot needs to reach Chess.com)
- A Chess.com account
- All the Python packages listed in the Makefile (don't worry, `make install` handles this)

## Installation

### 1. Install Dependencies

The quickest way is to use the Makefile:

```bash
make install
```

Or if you prefer to do it manually:

```bash
pip install Flask flask-cors pywebview DrissionPage stockfish colorama pyinstaller
```

### 2. Set Up Your Account

Create or edit `acc.json` with your Chess.com login credentials:

```json
{
  "username": "your_username",
  "password": "your_password"
}
```

Keep this file safe and don't share it!

## Usage

### Running the Bot

To start the bot as a Python script:

```bash
make
```

Or run it directly:

```bash
python main.py
```

The desktop app will launch, and you can monitor the bot's activity through the interface.

### Creating a Standalone Executable

Want to package everything into a single `.exe` file? Just run:

```bash
make build
```

You'll find your executable in the `dist/` folder, ready to share or deploy.

### Cleaning Up

To remove build artifacts and start fresh:

```bash
make clean
```

## Configuration

### config.json

This file stores your general preferences and settings:

- Where Stockfish is located on your computer
- Path to your Chrome browser
- Default engine strength (search depth)
- Any UI preferences you want to save

### session.json

The bot automatically manages this file to keep track of:

- Your active games
- Current board positions
- When you last used the bot

## How It Works

Here's what happens under the hood when you run the bot:

1. **Startup** - The bot loads Stockfish and opens your Chrome browser to Chess.com
2. **Browser Control** - DrissionPage takes over and navigates to your games
3. **Analysis** - Stockfish examines the board position and calculates the best move
4. **Execution** - The bot automatically plays the recommended move
5. **UI Updates** - The desktop interface shows what's happening in real-time

## API Endpoints

The bot's Flask backend provides several REST endpoints that the web interface uses to:

- Check the current board state
- Adjust the engine's thinking depth
- Tell the bot which move to play
- Switch between accounts
- View activity logs and debugging info

## Keyboard Shortcuts

See the "Keybinds" tab in the application UI for available shortcuts.

## Technical Details

Here's what powers this project:

- **Browser Automation**: DrissionPage handles all Chess.com interactions
- **Chess Engine**: Stockfish does the heavy lifting for move analysis
- **Backend**: Flask and Flask-CORS manage the API
- **Frontend**: Clean HTML5, CSS3, and JavaScript
- **Desktop Integration**: PyWebView wraps everything into a native-feeling app
- **Packaging**: PyInstaller bundles it all into a standalone executable

## Troubleshooting

**Stockfish not found?**
Don't worry—the app will automatically download and set it up on your first run.

**Can't find your browser?**
Make sure Chrome or Chromium is installed, or point the bot to your browser's location in the config file.

**Port already in use?**
If Flask can't start because the port is occupied, just change the port number in `main.py`.

## Important Notes

- The bot needs an active internet connection to reach Chess.com
- Keep your credentials in `acc.json` private—this is sensitive information
- You can adjust the engine strength using the search depth setting; higher numbers mean stronger play but take longer to think
- Make sure you're following Chess.com's terms of service before running this

## About

Created by mrmo7ox. Feel free to fork, modify, and improve this project!
