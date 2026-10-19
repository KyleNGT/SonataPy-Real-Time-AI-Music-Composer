# SonataPy - Real-time AI Music Generator

SonataPy streams AI-generated music in real time from text prompts, using Google's Lyria model. You steer the music with weighted prompts (for example "jazz piano" or "rock guitar") and controls such as BPM, scale, density and brightness.

The project has two parts:

- A browser frontend (`index.html`, `script.js`, `style.css`) that talks to the Lyria model.
- A small Python FastAPI server (`app.py`) that serves the frontend and runs a simple music DSL (tokenizer, parser, interpreter) through the `/interpret` endpoint.

## Project Structure

```
static/
  app.py            FastAPI server
  tokenizer.py      DSL lexer
  parser.py         DSL parser
  ast_nodes.py      AST node definitions
  interpreter.py    DSL interpreter
  index.html        Main interface
  splash_screen.html  Landing page
  script.js         Frontend logic
  style.css         Main styles
  splash.css        Splash screen styles
  assets/           Images
```

## Requirements

- Python 3.8 or newer
- A Google AI (Gemini) API key, available at https://aistudio.google.com/
- A modern browser (Chrome, Firefox, Edge or Safari) with internet access

## Setup

1. Open a terminal in the `static` folder of this repository.

2. Install the Python dependencies:

   ```bash
   pip install fastapi uvicorn
   ```

3. Start the server:

   ```bash
   python app.py
   ```

4. Open http://localhost:8000 in your browser.

When the page loads, it asks for your Google AI API key. The key is stored only in your browser's `sessionStorage` for the current session and is never saved in the project files.

## Usage

1. Type a prompt (such as "jazz piano") and add it. Each prompt gets a slider that sets its weight.
2. Adjust the settings: BPM, scale, density, brightness, and mute drums or bass.
3. Press Play to start streaming music. Press Pause or Stop to end it.
4. Use "Clear all" to reset the prompts and settings.

## Troubleshooting

- **Module not found:** run `pip install fastapi uvicorn` again.
- **Port 8000 already in use:** change the `port` value at the bottom of `app.py`, then open the new port in your browser.
- **No audio or API errors:** check that your API key is valid and has quota. To enter a new key, clear the site's session storage or open the page in a new tab or window.
- **Blank page:** open the browser developer console (F12) and look for errors.

## Security

- Never commit API keys to version control.
- For public deployments, keep the key on the server and proxy requests through the backend, because any key used in browser code can be read by users.
- The server currently allows requests from any origin (CORS `*`). Restrict this before deploying publicly.
