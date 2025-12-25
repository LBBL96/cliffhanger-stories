# Cliffhanger Stories

An interactive chatbot that tells serial adventure stories with cliffhangers that continue in the next chat session. Powered by AI (OpenAI or Anthropic).

## Features

- **Multiple AI Providers**: Choose between OpenAI (GPT-4) or Anthropic (Claude) models
- **Command-line Provider Selection**: Easily switch AI providers with a simple flag
- **Multiple Story Arcs**: Choose from different genre adventures
- **Interactive Storytelling**: Free-form exploration and choices
- **Responsive Web Interface**: Clean, modern UI
- **State Management**: Continue your story across sessions
- **Smart Context Tracking**: Prevents repetition and maintains story consistency

## Setup

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up your API keys by creating a `.env` file and  copying the example file
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and add your API keys:
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   OPENAI_MODEL=gpt-4o-2024-11-20
   
   ANTHROPIC_API_KEY=your-anthropic-api-key-here
   ANTHROPIC_MODEL=claude-opus-4-20250514
   ```

   # Choose default provider (optional, default is openai)
   ```
   AI_PROVIDER=openai
   ```
   
## Running the Application

### With OpenAI (default)
```bash
python app.py
```

### With Anthropic/Claude
```bash
python app.py --provider claude
```

### Start with Fresh Session
To clear your story progress and start fresh:
```bash
python app.py --reset
```

You can combine flags:
```bash
python app.py --provider claude --reset
```

### View Available Options
```bash
python app.py --help
```

Then open your web browser and navigate to `http://localhost:5006`

## AI Provider Configuration

The application supports two methods for selecting your AI provider:

1. **Command-line flag** (takes priority):
   - `--provider openai` - Use OpenAI GPT models
   - `--provider claude` - Use Anthropic Claude models

2. **Environment variable** in `.env`:
   - `AI_PROVIDER=openai` or `AI_PROVIDER=anthropic`

### Supported Models

**OpenAI:**
- Default: `gpt-4o-2024-11-20`
- Customizable via `OPENAI_MODEL` in `.env`

**Anthropic:**
- Default: `claude-opus-4-20250514`
- Customizable via `ANTHROPIC_MODEL` in `.env`

## Demo Mode (No API Key Required)

To see the UI themes without setting up OpenAI:
```bash
source venv/bin/activate
python demo_app.py
```
Then visit `http://localhost:5001`

## Project Structure

- `app.py` - Main Flask application and story logic
- `templates/index.html` - Web interface
- `static/` - Static files (CSS, JavaScript, images)
- `requirements.txt` - Python dependencies

## Adding New Stories

To add a new story, edit the `stories` list in `app.py` and add a new story arc with the following structure:

```python
{
    'title': 'Story Title',
    'intro': 'Introduction text',
    'scenes': [
        'Scene 1 text',
        'Scene 2 text',
        # ... more scenes
    ]
}
```

## License

This project is open source and available under the MIT License.
