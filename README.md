# Serial Adventure Bot

An interactive chatbot that tells serial adventure stories with cliffhangers that continue in the next chat session.

## Features

- Multiple story arcs to choose from
- Interactive storytelling with choices
- Visual elements for each scene
- Responsive web interface
- State management for continuing stories

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
4. Set up your OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
   Or create a `.env` file with:
   ```
   OPENAI_API_KEY=your-api-key-here
   ```
5. Create a `static/images` directory and add some images for the stories (naming them `story1_1.jpg`, `story1_2.jpg`, etc.)

## Running the Application

1. Activate the virtual environment:
   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Start the Flask server:
   ```bash
   python app.py
   ```
3. Open your web browser and navigate to `http://localhost:5000`
4. Select a story and begin your adventure!

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
