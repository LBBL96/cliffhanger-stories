from flask import Flask, render_template, jsonify, request, session
from flask_session import Session
from openai import OpenAI
import anthropic
import os
import argparse
from datetime import datetime
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Cliffhanger Stories - Interactive Adventure Game')
parser.add_argument('--provider', type=str, choices=['openai', 'claude'], default=None,
                    help='AI provider to use: "openai" (default) or "claude" (Anthropic)')
parser.add_argument('--reset', action='store_true',
                    help='Clear session data and start fresh')
args, unknown = parser.parse_known_args()

app = Flask(__name__)
app.secret_key = 'your-secret-key-for-sessions-change-in-production'

# Configure server-side session storage to handle large conversation histories
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './flask_session'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
Session(app)

# Handle session reset if --reset flag is provided
if args.reset:
    import shutil
    session_dir = os.path.join(os.path.dirname(__file__), 'flask_session')
    if os.path.exists(session_dir):
        shutil.rmtree(session_dir)
        print("✓ Session data cleared - starting fresh")
    else:
        print("✓ No existing session data found - starting fresh")

# AI Provider Configuration
# Priority: command-line flag > environment variable > default (openai)
if args.provider:
    # Map 'claude' to 'anthropic' internally
    AI_PROVIDER = 'anthropic' if args.provider == 'claude' else 'openai'
    print(f"AI provider set via command-line: {args.provider}")
else:
    AI_PROVIDER = os.getenv('AI_PROVIDER', 'openai').lower()
    if AI_PROVIDER not in ['openai', 'anthropic']:
        print(f"Warning: Invalid AI_PROVIDER '{AI_PROVIDER}' in .env, defaulting to 'openai'")
        AI_PROVIDER = 'openai'

# Initialize AI clients based on provider
if AI_PROVIDER == 'anthropic':
    anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
    ANTHROPIC_MODEL = os.getenv('ANTHROPIC_MODEL', 'claude-opus-4-20250514')
    print(f"Using Anthropic AI with model: {ANTHROPIC_MODEL}")
else:
    openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4o-2024-11-20')
    print(f"Using OpenAI with model: {OPENAI_MODEL}")

# In-memory storage for stories (in production, use a database)
stories = {}

class AdventureBot:
    def __init__(self):
        self.story_arcs = [
            {
                'title': 'The Algerian Eagle: A Nick Nolan Mystery',
                'canonical_facts': [
                    'The Algerian Eagle is a valuable statue made of gold and has ruby eyes',
                    'The statue contains a hidden compartment that uncle only found recently',
                    'The uncle bought the statue in Tangiers in the 1920s',
                    'The uncle\'s name is Harold',
                    'The uncle had an identical twin brother named Charles',
                    'Vivian Sterling does not know about her uncle\'s twin',
                    'Charles is hiding out at his brother Harold\'s mansion and Thomas is aware of it but is afraid to tell',
                    'Vivian Sterling\'s uncle was killed for the statue',
                    'Nick Nolan has an antique paperweight on his desk that his grandfather gave him',
                    'Nick\'s paperweight was a reward from Vivian\'s uncle Harold after his grandfather James saved Harold\'s life in the WWI',
                    'Vivian Sterling always calls Nick "Nicholas" - never "Nick" and everyone else calls him "Nick"',
                    'The butler\'s name is Thomas',
                    'The uncle owned a mansion',
                    'Lefty Torrino is a scarred smuggler who wears a fedora',
                    'The story takes place in 1940s San Francisco'
                ],
                'intro': 'The lady, Vivian Sterling, sits across from you at your desk, seeming not to notice the unkempt pile of papers covered in coffee cup rings and ashtrays overflowing with Marlboro butts. The amber light from your desk lamp catches the worry lines around her eyes as she speaks in measured tones about her uncle\'s death. "Someone killed him for a statue called the Algerian Eagle, Nicholas," she says, her voice barely above a whisper. The way she uses your full name sends a chill down your spine - nobody calls you Nicholas. You\'re just Nick, the guy people come to when they need something no one else can give them: answers.\n\nShe seems a little distracted as she reaches into her pocketbook, but hesitates just a moment when her eyes land on the antique paperweight on your desk. You never explain things to people, but it slips out anyway. "My grandfather gave that to me." She nods slightly in acknowledgement and turns her attention back to retrieving a leather billfold that turns out to be a checkbook. "I\'ll pay whatever it costs to get answers, Nicholas," she says quietly. You tell her you don\'t take money until you have something to give her - something you\'ve never said to a potential client before.',
                'scenes': [
                    'You decide to visit the uncle\'s mansion. The butler, a nervous wreck, claims he saw nothing. But you watch Vivian speak to him - she thanks him by name, asks how he\'s holding up, and lightly touches his arm when she sees his anxiety. "It\'s alright, Thomas," she says gently. There\'s genuine warmth there. Then you notice fresh cigarette butts - expensive Turkish tobacco. You\'ve never seen Vivian smoke, but someone was here recently. The plot thickens like fog rolling in from the bay. Do you ask Vivian about the cigarettes or investigate the butler\'s background?',
                    'Following a lead to the docks, you spot Vivian meeting with a scarred man in a fedora. She seems tense, unlike herself - you can see the strain in her posture as they speak quietly about "the bird" and you hear him growl "I got double-crossed." Suddenly, the scarred man pulls a gun! Do you intervene immediately, or stay hidden and follow whoever survives?',
                    'The scarred man is "Lefty" Torrino, a known smuggler. You tail him to a dusty import shop near the Barbary Coast where you overhear him talking on the telephone line: "The lady\'s getting too close. We gotta get rid of that detective." Your blood runs cold - they\'re talking about you! Do you call the cops, confront them alone, or set a trap?',
                    'You\'ve set up a meeting with Vivian at the old pier. She arrives with the Algerian Eagle, but so does Lefty with his gang. "I\'m sorry, Nicholas," Vivian says with genuine regret in her voice, "but some things are worth more than honor." Guns are drawn in the fog. After the confrontation ends, Vivian approaches you quietly. "That paperweight on your desk... my uncle gave it to your grandfather after your grandfather saved his life in the war. Uncle always said if I ever met a Nolan, I\'d know I could trust him with my life." You never thought of yourself as a noble character, but suddenly your posture straightens and you get a little emotional. It\'s not something obvious, just a shift in your mood, like a weight has been lifted and you know you\'ve carried on the legacy of being a worthy man. How do you respond to this revelation?'
                ]
            },
            {
                'title': 'Perils of Penelope: A Silent Movie Melodrama',
                'canonical_facts': [
                    'Penelope Pureheart is an orphaned heiress to the Pureheart Fortune',
                    'Snidely Whiplash is the villain with a magnificent mustache',
                    'Snidely holds a mortgage on the family farm',
                    'The story takes place in the early 1900s',
                    'Penelope has a dear sweet grandmother'
                ],
                'intro': 'Our story opens on sweet, innocent Penelope Pureheart, orphaned heiress to the Pureheart Fortune. But lurking in the shadows with his magnificent mustache and dastardly grin is the villainous Snidely Whiplash! He\'s got a mortgage on the family farm and evil plans brewing. Will our heroine escape his clutches?',
                'scenes': [
                    'Snidely has cornered Penelope in the old mill! "Pay the mortgage or lose the farm, my pretty!" he sneers, twirling his mustache. But wait - he\'s also holding a deed that would make him heir to everything if she can\'t pay! Penelope spots a rope hanging from the rafters. Does she try to swing to safety or attempt to grab the deed from his coat pocket?',
                    'Our heroine has escaped the mill, but Snidely gives chase on horseback! Penelope runs toward the railroad tracks where she knows the 3:15 train to Salvation City stops for water. But horror of horrors - Snidely has lassoed her! He\'s tying her to the very tracks as the distant whistle blows! Does she try to work the ropes loose with her hands or attempt to flag down the approaching train?',
                    'Penelope has freed one hand! The train is bearing down fast - she can see the engineer\'s horrified face and the piercing squeal of a 40-ton engine that\'s trying to stop in time to save her but won\'t be able to! But Snidely isn\'t done yet. He\'s placed a large boulder on the tracks ahead to derail the train! Our heroine must choose: finish freeing herself and jump clear, or stay tied and try to warn the train of the boulder ahead?',
                    'By a miracle, Penelope has warned the train and freed herself! But Snidely has one last card to play. He\'s kidnapped her dear sweet grandmother and taken her to his secret hideout in the abandoned mine! A note demands Penelope come alone with the deed to her fortune. Does she go alone as demanded, or try to rally the townspeople to help rescue Granny?',
                    'In the climactic showdown in the mine, Snidely has Granny tied up near a pile of dynamite! "Sign over the deed or the old lady gets it!" he cackles. But Penelope notices the fuse isn\'t lit and there\'s a pickaxe within reach. The question is: does she sign the deed to buy time, grab the pickaxe and fight, or try to untie Granny while Snidely gloats?'
                ]
            }
        ]
        self.current_scene = 0
        self.current_story = None
        self.conversation_history = []  # Track what has happened in current scene
        self.described_elements = set()  # Track what has already been described in this scene
        self.story_facts = []  # Track established facts and revelations that must remain consistent
        self.canonical_facts = []  # Immutable facts from the story definition

    def load_from_session(self):
        """Load bot state from Flask session"""
        if 'current_story_index' in session:
            story_index = session['current_story_index']
            self.current_story = self.story_arcs[story_index]
            self.current_scene = session.get('current_scene', 0)
            self.conversation_history = session.get('conversation_history', [])
            self.described_elements = set(session.get('described_elements', []))
            self.story_facts = session.get('story_facts', [])
            self.canonical_facts = self.current_story.get('canonical_facts', [])
            print(f"Loaded from session: story={self.current_story['title']}, scene={self.current_scene}, history items={len(self.conversation_history)}")
            if self.conversation_history:
                print(f"DEBUG: Last conversation item: '{self.conversation_history[-1]['user'][:30]}...'")
            else:
                print("DEBUG: No conversation history found in session")
        else:
            print("No session data found")
            self.conversation_history = []
            self.described_elements = set()
            self.story_facts = []

    def save_to_session(self):
        """Save bot state to Flask session"""
        if self.current_story:
            story_index = self.story_arcs.index(self.current_story)
            session['current_story_index'] = story_index
            session['current_scene'] = self.current_scene
            session['conversation_history'] = self.conversation_history
            session['described_elements'] = list(self.described_elements)
            session['story_facts'] = self.story_facts
            # canonical_facts don't need to be saved - they're loaded from story definition
            print(f"Saved to session: story_index={story_index}, scene={self.current_scene}, history items={len(self.conversation_history)}")
            if self.conversation_history:
                print(f"DEBUG: Saving last conversation: '{self.conversation_history[-1]['user'][:30]}...'")
            else:
                print("DEBUG: Saving empty conversation history")
        else:
            session.pop('current_story_index', None)
            session.pop('current_scene', None)
            session.pop('conversation_history', None)
            session.pop('described_elements', None)
            session.pop('story_facts', None)
            print("Cleared session data")

    def start_story(self, story_index):
        print(f"start_story called with index: {story_index}")
        self.current_story = self.story_arcs[story_index]
        self.current_scene = 0
        self.conversation_history = []  # Clear history for new story
        self.described_elements = set()  # Clear described elements
        self.story_facts = []  # Clear story facts
        self.canonical_facts = self.current_story.get('canonical_facts', [])  # Load immutable facts
        
        # Extract elements from intro text to prevent repetition
        intro_text = self.current_story['intro']
        self.extract_described_elements(intro_text, 0)
        
        print(f"Story set to: {self.current_story['title']}, scene: {self.current_scene}")
        self.save_to_session()
        return {
            'message': intro_text + "\n\nWhat do you want to do next?",
            'image': f'story{story_index+1}_1.jpg'
        }

    def next_scene(self, choice=None):
        print(f"next_scene called: current_story={self.current_story is not None}, current_scene={self.current_scene}")
        if not self.current_story:
            print("No current story - returning to story selection")
            return {
                'message': 'Please select a story first.',
                'end': True
            }
        
        # Check if we've gone through all predefined scenes
        if self.current_scene >= len(self.current_story['scenes']):
            return {
                'message': 'You have experienced all the main story scenes. The adventure continues based on your choices and actions.\n\nWhat do you want to do next?',
            }
        
        # Advance to next scene first
        self.current_scene += 1
        
        # Clear described elements when changing scenes
        self.described_elements = set()
        
        # Get the scene outline for the NEW scene
        scene_outline = self.current_story['scenes'][self.current_scene - 1]
        
        # Generate rich content using AI
        generated_content = self.generate_scene_content(scene_outline, self.current_story)
        
        # Filter conversation history and save
        self.filter_history_for_scene_change()
        self.save_to_session()
        
        response = {
            'message': generated_content + "\n\nWhat do you want to do next?",
            'image': f'story{self.story_arcs.index(self.current_story)+1}_{self.current_scene}.jpg'
        }
        return response

    def filter_history_for_scene_change(self):
        """Keep important story elements, remove location-specific actions"""
        if not self.conversation_history:
            return
        
        # Keywords that indicate important story information to keep
        keep_keywords = [
            'said', 'told', 'mentioned', 'revealed', 'explained', 'admitted',
            'confessed', 'whispered', 'asked about', 'learned', 'discovered',
            'nicholas', 'vivian', 'uncle', 'algerian eagle', 'statue', 'murder',
            'trust', 'suspicious', 'relationship', 'connection', 'secret'
        ]
        
        # Keywords that indicate location-specific actions to remove
        remove_keywords = [
            'examined', 'looked at', 'walked to', 'opened', 'closed', 'touched',
            'picked up', 'put down', 'sat down', 'stood up', 'leaned', 'moved',
            'desk', 'chair', 'door', 'window', 'lamp', 'drawer', 'shelf'
        ]
        
        filtered_history = []
        for interaction in self.conversation_history:
            user_input = interaction['user'].lower()
            response = interaction['response'].lower()
            
            # Check if this interaction contains important story information
            has_story_info = any(keyword in user_input or keyword in response for keyword in keep_keywords)
            has_location_action = any(keyword in user_input for keyword in remove_keywords)
            
            # Keep if it has story info and isn't just a location action
            if has_story_info and not has_location_action:
                filtered_history.append(interaction)
        
        # Keep the most recent 10 important interactions when changing scenes
        # This maintains continuity while filtering out location-specific details
        self.conversation_history = filtered_history[-10:] if filtered_history else []
        print(f"Filtered history for scene change: kept {len(self.conversation_history)} important interactions")

    def extract_story_facts(self, content, user_input):
        """Extract important story facts that must remain consistent"""
        # Track quoted dialogue - anything in quotes is what a character said
        import re
        quoted_dialogue = re.findall(r'"([^"]+)"', content)
        for quote in quoted_dialogue:
            if len(quote) > 10 and len(quote) < 250:
                # Store the quote with context about who might be speaking
                fact = f'Character said: "{quote}"'
                self.story_facts.append(fact)
                print(f"DEBUG: Tracked dialogue: {quote[:60]}...")
        
        # Extract key sentences that contain factual information
        sentences = content.replace('!', '.').replace('?', '.').split('.')
        for sentence in sentences:
            sentence = sentence.strip()
            sentence_lower = sentence.lower()
            
            # Track any character mentions or introductions
            if any(word in sentence_lower for word in ['dr.', 'doctor', 'professor', 'mr.', 'mrs.', 'miss', 'detective', 'officer']):
                if len(sentence) > 15 and len(sentence) < 250:
                    self.story_facts.append(sentence)
                    print(f"DEBUG: Tracked character mention: {sentence[:80]}...")
            
            # Track statements about what characters say or know
            elif any(word in sentence_lower for word in ['said', 'told', 'admitted', 'revealed', 'described', 'mentioned', 'claims', 'insists', 'denies', 'confirms', 'knows', 'doesn\'t know', 'heard']):
                if len(sentence) > 20 and len(sentence) < 250:
                    self.story_facts.append(sentence)
                    print(f"DEBUG: Tracked statement: {sentence[:80]}...")
            
            # Track discoveries and observations
            elif any(word in sentence_lower for word in ['find', 'found', 'discover', 'notice', 'see', 'reveal', 'spotted', 'observed']):
                if len(sentence) > 20 and len(sentence) < 250:
                    self.story_facts.append(sentence)
                    print(f"DEBUG: Tracked discovery: {sentence[:80]}...")
            
            # Track character relationships and connections
            elif any(word in sentence_lower for word in ['brother', 'sister', 'uncle', 'aunt', 'father', 'mother', 'friend', 'colleague', 'partner', 'associate']):
                if len(sentence) > 15 and len(sentence) < 250:
                    self.story_facts.append(sentence)
                    print(f"DEBUG: Tracked relationship: {sentence[:80]}...")
        
        # Keep only the most recent 40 facts for comprehensive tracking
        # This ensures we don't lose important character statements and discoveries
        if len(self.story_facts) > 40:
            self.story_facts = self.story_facts[-40:]

    def extract_described_elements(self, content, scene_number):
        """Extract and track elements that have been described to prevent repetition"""
        # Common descriptive keywords to track
        descriptive_patterns = [
            'gray eyes', 'honey-colored hair', 'honey colored hair', 'lilac perfume', 'sapphire ring',
            'amber light', 'desk lamp', 'coffee cup rings', 'coffee rings', 'ashtrays',
            'tall for a woman', 'head shorter', 'elegant', 'refined', 'composed',
            'fog', 'bay', 'docks', 'mansion', 'study', 'library', 'parlor',
            'butler', 'Thomas', 'nervous', 'wreck', 'nervous wreck',
            'leaning back', 'toying with', 'checkbook', 'pocketbook',
            'Turkish tobacco', 'cigarette butts', 'Marlboro',
            'office', 'filing cabinets', 'papers',
            'scarred', 'fedora', 'lefty', 'torrino'
        ]
        
        content_lower = content.lower()
        for pattern in descriptive_patterns:
            if pattern.lower() in content_lower:
                self.described_elements.add(pattern)
                print(f"DEBUG: Tracked described element: '{pattern}'")
        
        # Track character names when they're described with physical details
        if 'vivian' in content_lower and any(word in content_lower for word in ['eyes', 'hair', 'perfume', 'jewelry', 'ring', 'tall', 'elegant', 'refined']):
            self.described_elements.add('Vivian appearance')
            print(f"DEBUG: Tracked Vivian appearance description")
        
        if 'nick' in content_lower and any(word in content_lower for word in ['tall', 'dark', 'rugged', 'handsome', 'fit']):
            self.described_elements.add('Nick appearance')
            print(f"DEBUG: Tracked Nick appearance description")
        
        # Track Thomas descriptions specifically
        if 'thomas' in content_lower and any(word in content_lower for word in ['nervous', 'wreck', 'butler', 'anxious', 'worried', 'frightened', 'scared']):
            self.described_elements.add('Thomas description')
            print(f"DEBUG: Tracked Thomas description")
        
        # Track Lefty descriptions
        if any(name in content_lower for name in ['lefty', 'torrino']) and any(word in content_lower for word in ['scarred', 'scar', 'fedora', 'hat', 'smuggler']):
            self.described_elements.add('Lefty description')
            print(f"DEBUG: Tracked Lefty description")
        
        # Track setting descriptions
        if scene_number == 0 and any(word in content_lower for word in ['office', 'desk', 'lamp', 'filing']):
            self.described_elements.add('office setting')
        elif scene_number == 1 and any(word in content_lower for word in ['mansion', 'parlor', 'library', 'elegant']):
            self.described_elements.add('mansion setting')
        elif scene_number == 2 and any(word in content_lower for word in ['fog', 'docks', 'bay', 'pier']):
            self.described_elements.add('docks setting')
        
        print(f"DEBUG: Total described elements tracked: {len(self.described_elements)} items: {sorted(self.described_elements)}")

    def extract_choices_from_outline(self, scene_outline):
        """Extract choice options from the scene outline"""
        # Look for the question and choices at the end of the outline
        if "Do you " in scene_outline:
            # Find the part after "Do you" which contains the choices
            question_part = scene_outline.split("Do you ")[-1]
            
            # Split on " or " to get individual choices
            if " or " in question_part:
                choices_text = question_part.split("?")[0]  # Remove anything after the question mark
                choices = [choice.strip() for choice in choices_text.split(" or ")]
                return choices
        
        # Fallback to generic continue option
        return ['Continue...']

    def handle_user_input(self, user_input):
        """Handle free-form user input like questions, actions, or choices"""
        print(f"handle_user_input called: current_story={self.current_story is not None}, current_scene={self.current_scene}")
        if not self.current_story:
            print("No current story in handle_user_input - returning to story selection")
            print("DEBUG: Story state lost in user input handling")
            return {
                'message': 'Please select a story first to begin your adventure.',
                'end': True
            }
        
        # Generate contextual response using AI
        response_content = self.generate_contextual_response(user_input)
        
        # Add this interaction to conversation history
        self.conversation_history.append({
            'user': user_input,
            'response': response_content
        })
        
        # Keep last 15 interactions for strong continuity
        # Flask sessions can handle this without cookie size issues
        if len(self.conversation_history) > 15:
            self.conversation_history = self.conversation_history[-15:]
        
        print(f"DEBUG: Added to history. Total interactions: {len(self.conversation_history)}")
        print(f"DEBUG: Latest interaction - User: '{user_input[:50]}...'")
        
        # Save updated history
        self.save_to_session()
        
        # Check if we've reached the end of predefined scenes
        if self.current_scene >= len(self.current_story['scenes']):
            # Continue with open-ended adventure
            return {
                'message': response_content + "\n\nWhat do you want to do next?"
            }
        
        return {
            'message': response_content + "\n\nWhat do you want to do next?"
        }


    def generate_contextual_response(self, user_input):
        """Generate a contextual response to user input using AI"""
        try:
            style_prompt = self.get_story_style_prompt(self.current_story['title'])
            
            # Get current scene context and location
            current_scene_outline = ""
            scene_location = ""
            scene_characters = ""
            
            print(f"DEBUG: Generating response for scene {self.current_scene}")
            print(f"DEBUG: User input: '{user_input[:50]}...'")
            
            if self.current_scene == 0:
                # Intro scene - Nick's office
                current_scene_outline = self.current_story['intro']
                scene_location = "Nick Nolan's detective office in 1940s San Francisco"
                scene_characters = "Nick Nolan (you) and Vivian Sterling"
                print(f"DEBUG: Scene 0 - Office setting")
            elif self.current_scene < len(self.current_story['scenes']):
                current_scene_outline = self.current_story['scenes'][self.current_scene - 1]
                # Determine location based on scene number
                if self.current_scene == 1:
                    scene_location = "The uncle's mansion - elegant but somber"
                    scene_characters = "Nick Nolan (you), Vivian Sterling, and Thomas the butler"
                    print(f"DEBUG: Scene 1 - Mansion setting")
                elif self.current_scene == 2:
                    scene_location = "The foggy docks near San Francisco Bay"
                    scene_characters = "Nick Nolan (you), Vivian Sterling, and Lefty Torrino"
                    print(f"DEBUG: Scene 2 - Docks setting")
                elif self.current_scene == 3:
                    scene_location = "Dusty import shop near the Barbary Coast"
                    scene_characters = "Nick Nolan (you) and Lefty Torrino"
                    print(f"DEBUG: Scene 3 - Import shop setting")
                else:
                    scene_location = "Various locations in 1940s San Francisco"
                    scene_characters = "Nick Nolan (you) and other characters"
            
            system_message = f"""You are an interactive storyteller for a text adventure game.

{style_prompt}

CURRENT STORY CONTEXT:
Title: {self.current_story['title']}
Current scene: {current_scene_outline}
Scene location: {scene_location}
Characters present: {scene_characters}

SCENE LOCK - YOU ARE CURRENTLY IN SCENE {self.current_scene}:
- You MUST stay in this scene location until explicitly told to advance
- You CANNOT jump to other scenes (office, mansion, docks, shop) 
- All exploration happens WITHIN the current scene location
- DO NOT generate content from other scene numbers
Scene Description: {current_scene_outline}

INTERACTIVE INSTRUCTIONS:
1. This is a pure text adventure - respond to ANY user action or question
2. The user can explore, investigate, talk to characters, or try creative actions
3. Respond in character and maintain the story's atmosphere
4. Describe results of actions realistically within the story world
5. Keep responses engaging and immersive (1-2 paragraphs)
6. Always stay true to the genre and time period
7. Be creative - allow unexpected actions and consequences
8. Format with clear paragraph breaks - use double line breaks between paragraphs
9. End responses naturally without suggesting specific choices
10. ALWAYS complete your sentences - never end mid-sentence or mid-thought

DIALOGUE TRACKING (CRITICAL):
11. When a character speaks, use quotation marks: "Like this"
12. ANYTHING IN QUOTES is what the character SAID OUT LOUD
13. Characters are BOUND by what they say in quotes - if Vivian says "I don't know Dr. Whitmore," she DOESN'T know him
14. Track character knowledge based on quoted dialogue
15. You can write dialogue without speech tags: She shifts. "I don't know him." Her voice wavers.
16. But ALWAYS use quotes for actual speech so we can track what characters know and claim

CRITICAL ANTI-REPETITION RULES:
11. NEVER re-describe settings, rooms, or locations that have already been described
12. NEVER re-mention character physical appearances (eyes, hair, height, perfume, jewelry) once established
13. NEVER re-describe objects, furniture, or atmospheric details already mentioned
14. DO NOT repeat phrases like "gray eyes", "honey-colored hair", "lilac perfume", "sapphire ring"
15. DO NOT re-describe the room ambiance, lighting, or general setting
16. When a character speaks or acts, focus ONLY on: what they say/do NOW, new information revealed, plot advancement
17. Assume setting and character appearances are already established - skip all physical descriptions
18. If you must reference a character, use their name only - no descriptive modifiers
19. Each response should contain ONLY: new dialogue, new actions, new discoveries, plot progression
20. Think: "What's NEW in this moment?" - describe ONLY that

LOCATION COMPLIANCE IS MANDATORY - You MUST stay in the specified location and NEVER mix elements from other scenes"""

            # Create location-specific context
            location_context = ""
            if self.current_scene == 0:
                location_context = """LOCATION: Nick's detective office in San Francisco (SCENE 0)
- SETTING: Indoor office with desk, chairs, filing cabinets, desk lamp
- ATMOSPHERE: Gritty, urban, cigarette smoke, coffee stains
- CHARACTERS PRESENT: Only Nick and Vivian
- ABSOLUTELY NO: Fog, bay sounds, docks, water, pylons, foghorns, mansion elements, butlers, Thomas
- YOU ARE IN AN OFFICE - NOT at mansion, not at docks, not anywhere else"""
            elif self.current_scene == 1:
                location_context = """MANSION EXPLORATION LOCK (SCENE 1 ONLY):
- YOU ARE INSIDE THE UNCLE'S MANSION - A WEALTHY INDOOR HOME
- MANSION ROOMS: Library, parlor, dining room, study, east wing, west wing, servants' quarters
- MANSION OBJECTS: Ashtrays with cigarettes, bookshelves, paintings, furniture, carpets, chandeliers
- CHARACTERS HERE: You (Nick), Vivian Sterling, Thomas the butler
- EXPLORATION STAYS IN MANSION: Looking at cigarettes = mansion cigarettes, going to east wing = mansion east wing
- ZERO DOCKS CONTENT: No fog, no bay, no ships, no pylons, no maritime anything
- IF USER EXPLORES MANSION, RESPONSE STAYS IN MANSION - DO NOT JUMP TO DOCKS SCENE
- MANSION ONLY - MANSION ONLY - MANSION ONLY"""
            elif self.current_scene == 2:
                location_context = """LOCATION: Foggy docks by San Francisco Bay (OUTDOOR)
- SETTING: Waterfront with fog, bay sounds, pylons, piers, ships
- ATMOSPHERE: Misty, maritime, salt air, water lapping, foghorns
- NO: Mansion elements, office furniture, indoor settings"""
            elif self.current_scene == 3:
                location_context = """LOCATION: Dusty import shop near Barbary Coast (INDOOR)
- SETTING: Commercial shop with shelves, imported goods, dusty atmosphere
- ATMOSPHERE: Commercial, cramped, merchandise displays
- NO: Fog, docks, bay sounds, mansion elements, office furniture"""
            else:
                location_context = f"""LOCATION: {scene_location}
- Stay consistent with this specific location
- Do not mix elements from other scenes"""

            # Build conversation history context
            history_context = ""
            if self.conversation_history:
                print(f"DEBUG: Building history context with {len(self.conversation_history)} interactions")
                print(f"DEBUG: Conversation history items: {[h['user'][:50] for h in self.conversation_history]}")
                history_context = """📜 CONVERSATION HISTORY - EVERYTHING THAT HAS HAPPENED IN THIS SCENE:
(Characters REMEMBER all of this. You MUST maintain continuity with these exchanges.)

"""
                for i, interaction in enumerate(self.conversation_history, 1):
                    # Include FULL conversation, not truncated
                    history_context += f"Exchange {i}:\n"
                    history_context += f"Player asked/did: {interaction['user']}\n"
                    history_context += f"You responded: {interaction['response']}\n"
                    history_context += "---\n\n"
                    print(f"DEBUG: Added exchange {i} to context - User: '{interaction['user'][:40]}...'")
                history_context += """⚠️ CRITICAL CONTINUITY RULES:
- Characters REMEMBER everything from these exchanges
- QUOTED DIALOGUE = CHARACTER SPEECH: Anything in quotes is what a character said out loud
- If a character mentioned someone (like Dr. Whitmore), they KNOW about them in future responses
- If a character said something in quotes, they SAID IT - track their knowledge accordingly
- If information was revealed, it STAYS revealed - don't contradict it
- Build on what was said, don't reset or forget
- Maintain consistent character knowledge and awareness
- Example: If Vivian said "I don't know any Dr. Whitmore" then she DOESN'T know Dr. Whitmore

"""
            else:
                print("DEBUG: No conversation history available for context")

            # Build list of already described elements
            already_described = ""
            if self.described_elements:
                already_described = f"""🚫 ALREADY DESCRIBED IN THIS SCENE - ABSOLUTELY DO NOT MENTION AGAIN:
{', '.join(sorted(self.described_elements))}

⚠️ CRITICAL: You MUST NOT re-describe any of these elements. 
- If "Thomas description" is listed, DO NOT describe Thomas as nervous, a wreck, anxious, etc.
- If "Vivian appearance" is listed, DO NOT mention her eyes, hair, perfume, or jewelry
- If character descriptions are listed, refer to them by NAME ONLY with NO descriptive words
- Focus ONLY on what is NEW in this moment - new actions, new dialogue, new discoveries
- Example: Write "Thomas speaks" NOT "The nervous butler speaks"
"""

            # Build list of canonical facts (immutable from story definition)
            canonical_facts_context = ""
            if self.canonical_facts:
                canonical_facts_context = """⚠️ CANONICAL STORY FACTS - ABSOLUTELY IMMUTABLE (NEVER CHANGE THESE):
"""
                for i, fact in enumerate(self.canonical_facts, 1):
                    canonical_facts_context += f"{i}. {fact}\n"
                canonical_facts_context += """
🔒 LOCKED: These facts are PERMANENT and UNCHANGEABLE. They define the core story elements.
- Character names NEVER change (Thomas is always Thomas, Vivian is always Vivian)
- The Algerian Eagle is ALWAYS the statue's name - never "Maltese Falcon" or any other name
- Vivian's uncle was killed - this NEVER changes
- The paperweight connection NEVER changes
- ALL canonical facts must be referenced EXACTLY as written above

"""

            # Build list of established story facts that must remain consistent
            story_facts_context = ""
            if self.story_facts:
                story_facts_context = """ESTABLISHED FACTS FROM GAMEPLAY - THESE MUST REMAIN CONSISTENT:
"""
                for i, fact in enumerate(self.story_facts, 1):
                    story_facts_context += f"{i}. {fact}\n"
                story_facts_context += """
CRITICAL: These facts emerged during gameplay and are LOCKED IN. You CANNOT contradict them. If a character said they saw something, they cannot later deny it. If evidence was discovered, it stays discovered. Build on these facts, don't reverse them.

"""

            user_message = f"""USER INPUT: {user_input}

LOCATION CONTEXT: {location_context}

{already_described}

{canonical_facts_context}{story_facts_context}

{history_context}Respond to this input with NEW content that continues from where we left off:"""

            # Generate response using configured AI provider
            # Lower temperature (0.5) for more consistent, factual responses
            if AI_PROVIDER == 'anthropic':
                response = anthropic_client.messages.create(
                    model=ANTHROPIC_MODEL,
                    max_tokens=600,
                    temperature=0.5,
                    system=system_message,
                    messages=[
                        {"role": "user", "content": user_message}
                    ]
                )
                content = response.content[0].text
            else:
                response = openai_client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=600,
                    temperature=0.5
                )
                content = response.choices[0].message.content
            
            # Check if response was cut off mid-sentence
            if content and not content.rstrip().endswith(('.', '!', '?', '"', "'", '...', ':')):
                # Add ellipsis if it seems incomplete
                content = content.rstrip() + "..."
            
            # Track described elements to prevent repetition
            self.extract_described_elements(content, self.current_scene)
            
            # Track story facts to prevent contradictions
            self.extract_story_facts(content, user_input)
            
            return content
            
        except Exception as e:
            print(f"AI contextual response failed: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return f"AI Error: {str(e)}\n\nI understand you said '{user_input}'. What would you like to do next?"

    def get_story_style_prompt(self, story_title):
        """Get the appropriate style prompt based on story type"""
        if "Nick Nolan Mystery" in story_title:
            return """
You are writing a 1940s noir detective story in the style of Dashiell Hammett and Raymond Chandler. 

CRITICAL PERIOD ACCURACY (1940s):
- NO modern technology: no computers, cell phones, modern cars, credit cards, or anything invented after 1940
- Use period-appropriate items: rotary phones, telegrams, typewriters, fountain pens, cash transactions
- Transportation: 1930s-1940s automobiles, streetcars, trains, walking
- Communication: telephone calls, letters, telegrams, face-to-face meetings
- Lighting: incandescent bulbs, desk lamps, street lamps, neon signs
- Clothing: suits, fedoras, overcoats, dresses appropriate to the era
- Weapons: revolvers, automatics common to the 1940s (no modern firearms)

CHARACTER DESCRIPTIONS (USE THESE EXACT DETAILS - DO NOT INVENT NEW ONES):
- Nick Nolan (you): Tall, dark, fit, and ruggedly good looking. The kind of man women stare at without him even noticing. Hard-boiled detective with integrity.
- Vivian Sterling: Gray eyes, honey-colored hair. Tall for a woman but a head shorter than Nick. Wears faint lilac-scented perfume. Only jewelry is a sapphire ring on her right hand. Elegant, refined, calm, and composed. Speaks with quiet dignity and grace, never bitter or hard-edged. She doesn't seem to notice that she is being noticed.
- Thomas: The butler at the uncle's mansion. Nervous disposition.
- Lefty Torrino: Scarred smuggler who wears a fedora.

NAMING CONSISTENCY (ABSOLUTELY CRITICAL - NEVER VIOLATE):
- Vivian Sterling ALWAYS calls him "Nicholas" - NEVER "Nick"
- ALL other characters call him "Nick" - NEVER "Nicholas"
- The butler is ALWAYS named "Thomas" - never any other name
- The statue is ALWAYS "the Algerian Eagle" - never "Maltese Falcon" or any other name
- Vivian's relative is ALWAYS "uncle" - never father, brother, or any other relation
- This naming pattern is a key character trait and plot element

CONSISTENCY ENFORCEMENT:
- If you mention the statue, it MUST be called "the Algerian Eagle"
- If you mention the butler, he MUST be called "Thomas"
- If Vivian speaks to Nick, she MUST say "Nicholas"
- The uncle's death and the paperweight connection are FIXED story elements
- DO NOT invent new names, relationships, or backstories that contradict established facts

STYLE REQUIREMENTS:
- Write in second person ("you")
- Use atmospheric, gritty descriptions with fog, rain, shadows
- Include authentic 1940s language and slang (dame, gumshoe, copper, etc.)
- NEVER mention character details more than once per scene
- DO NOT invent new physical details, jewelry, scents, or eye colors - use only what's specified above
- Other characters use period-appropriate street language
- Build tension and suspense
- Include sensory details (sounds, smells, textures)
- Keep the noir atmosphere dark but not hopeless

TONE: Sophisticated, atmospheric, morally complex but ultimately honorable
LENGTH: 2-3 paragraphs with rich detail
"""
        elif "Silent Movie" in story_title:
            return """
You are writing a classic silent movie melodrama in the style of early 1900s adventure serials.

CRITICAL PERIOD ACCURACY (1900-1910):
- NO modern technology: no automobiles (horse-drawn carriages only), no electric lights in rural areas, no modern appliances
- Use period-appropriate items: oil lamps, candles, wood stoves, iceboxes, hand-pumped wells
- Transportation: horses, horse-drawn carriages, trains, walking, bicycles
- Communication: handwritten letters, telegrams, face-to-face meetings, town criers
- Lighting: oil lamps, candles, gas lights in cities, fireplaces
- Clothing: long dresses, bustles, bonnets, top hats, waistcoats, pocket watches
- Weapons: single-shot rifles, revolvers, dynamite (no modern explosives or firearms)
- Rural setting: farms, mills, small towns, dirt roads, wooden buildings

STYLE REQUIREMENTS:
- Write in second person ("you") 
- Use dramatic, over-the-top language with exclamation points
- Include classic melodrama elements: dastardly villains, heroic rescues, dramatic reversals
- Penelope Pureheart is sweet, innocent, but surprisingly resourceful
- Snidely Whiplash is a mustache-twirling villain with grandiose schemes
- Use period-appropriate language and situations (no modern slang)
- Build excitement and suspense
- Include vivid action descriptions
- Keep the tone adventurous and wholesome despite the perils

TONE: Melodramatic, exciting, wholesome adventure with clear heroes and villains
LENGTH: 2-3 paragraphs with vivid action
"""
        return ""

    def generate_scene_content(self, scene_outline, story_context):
        """Generate rich content from scene outline using ChatGPT"""
        try:
            style_prompt = self.get_story_style_prompt(self.current_story['title'])
            
            # Build canonical facts context for scene generation
            canonical_facts_for_scene = ""
            if self.canonical_facts:
                canonical_facts_for_scene = "\n⚠️ CANONICAL STORY FACTS (NEVER CHANGE):\n"
                for fact in self.canonical_facts:
                    canonical_facts_for_scene += f"- {fact}\n"
            
            # Structured for optimal caching - system message contains cacheable content
            system_message = f"""You are a master storyteller specializing in classic genre fiction.

{style_prompt}

STORY CONTEXT:
Title: {self.current_story['title']}
Previous scenes have established the characters and setting.
{canonical_facts_for_scene}

STANDARD INSTRUCTIONS:
1. Expand this outline into a rich, detailed scene
2. Add atmospheric descriptions, dialogue, and sensory details
3. Maintain the established character voices and relationships
4. Build tension leading to the choice moment
5. DO NOT include the choice options in your response - end just before the choices
6. Stay true to the genre and time period
7. End with suspense that leads naturally to decision-making
8. CRITICAL: Use EXACT names from canonical facts - never invent alternatives
8. Format with clear paragraph breaks - use double line breaks between paragraphs
9. ALWAYS complete your sentences - never end mid-sentence or mid-thought
10. Focus on NEW story elements and progression - avoid repeating previous scene descriptions"""

            # User message contains the variable content
            user_message = f"""SCENE OUTLINE TO EXPAND:
{scene_outline}

Generate the expanded scene now:"""

            # Generate response using configured AI provider
            # Lower temperature (0.5) for scene generation to maintain consistency
            if AI_PROVIDER == 'anthropic':
                response = anthropic_client.messages.create(
                    model=ANTHROPIC_MODEL,
                    max_tokens=1000,
                    temperature=0.5,
                    system=system_message,
                    messages=[
                        {"role": "user", "content": user_message}
                    ]
                )
                content = response.content[0].text
                
                # Log usage statistics for Anthropic
                usage = response.usage
                input_tokens = usage.input_tokens
                output_tokens = usage.output_tokens
                
                # Anthropic pricing (Claude 3.5 Sonnet)
                input_cost = input_tokens * 0.003 / 1000
                output_cost = output_tokens * 0.015 / 1000
                total_cost = input_cost + output_cost
                
                print(f"Usage: {input_tokens} input, {output_tokens} output")
                print(f"Cost: ${total_cost:.4f}")
            else:
                response = openai_client.chat.completions.create(
                    model=OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=1000,
                    temperature=0.5
                )
                
                # Log usage statistics including caching
                usage = response.usage
                total_tokens = usage.total_tokens
                
                # Check for cached tokens (available in newer API responses)
                cached_tokens = 0
                if hasattr(usage, 'prompt_tokens_details') and usage.prompt_tokens_details:
                    cached_tokens = getattr(usage.prompt_tokens_details, 'cached_tokens', 0)
                
                # Calculate costs
                input_cost = (usage.prompt_tokens - cached_tokens) * 0.0025 / 1000  # Regular input tokens
                cached_cost = cached_tokens * 0.00125 / 1000  # Cached tokens (50% discount)
                output_cost = usage.completion_tokens * 0.01 / 1000
                total_cost = input_cost + cached_cost + output_cost
                
                print(f"Usage: {usage.prompt_tokens} input ({cached_tokens} cached), {usage.completion_tokens} output")
                print(f"Cost: ${total_cost:.4f} (saved ${cached_tokens * 0.00125 / 1000:.4f} from caching)")
                
                content = response.choices[0].message.content
            
            # Check if response was cut off mid-sentence
            if content and not content.rstrip().endswith(('.', '!', '?', '"', "'", '...', ':')):
                # Add ellipsis if it seems incomplete
                content = content.rstrip() + "..."
            
            # Track described elements from generated scene to prevent repetition
            self.extract_described_elements(content, self.current_scene)
            
            return content
            
        except Exception as e:
            # Fallback to original outline if AI fails
            print(f"AI generation failed: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
            return f"AI Error: {str(e)}\n\nFallback: {scene_outline}"

bot = AdventureBot()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/stories', methods=['GET'])
def get_stories():
    return jsonify([{'id': i, 'title': story['title']} for i, story in enumerate(bot.story_arcs)])

@app.route('/api/start/<int:story_id>', methods=['POST'])
def start_story(story_id):
    bot.load_from_session()
    return jsonify(bot.start_story(story_id))

@app.route('/api/next', methods=['POST'])
def next_scene():
    bot.load_from_session()
    data = request.get_json()
    return jsonify(bot.next_scene(data.get('choice')))

@app.route('/api/user-input', methods=['POST'])
def handle_user_input():
    bot.load_from_session()
    data = request.get_json()
    user_input = data.get('input')
    return jsonify(bot.handle_user_input(user_input))


if __name__ == '__main__':
    app.run(debug=True, port=5006)
