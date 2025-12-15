"""
AI D&D Text RPG - Simple Chat Loop (Phase 1, Step 1.1)
A basic conversation loop where AI acts as Dungeon Master.
"""

import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env
load_dotenv()

# System prompt that defines the AI as a Dungeon Master
DM_SYSTEM_PROMPT = """You are an experienced Dungeon Master running a classic D&D adventure.

Your responsibilities:
- Narrate the story in an engaging, immersive way
- Describe environments, NPCs, and events vividly
- Respond to player actions and decisions
- Keep the adventure exciting and fair
- Ask for dice rolls when appropriate (you'll handle the mechanics later)

Style guidelines:
- Use second person ("You enter the tavern...")
- Be descriptive but concise
- Create tension and mystery
- Encourage player creativity

Start by welcoming the player and setting the scene for their adventure.
"""


def create_client():
    """Configure and return the Gemini model."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set.")
        print("Please add it to your .env file: GOOGLE_API_KEY=your-api-key-here")
        exit(1)
    
    genai.configure(api_key=api_key)
    
    # Get model name from env or use default
    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    
    # Create the model with system instruction
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=DM_SYSTEM_PROMPT
    )
    
    return model


def get_dm_response(chat, player_input):
    """Get a response from the AI Dungeon Master."""
    try:
        response = chat.send_message(player_input)
        return response.text
    except Exception as e:
        return f"[DM Error: {str(e)}]"


def main():
    """Main game loop."""
    print("=" * 60)
    print("       AI D&D TEXT RPG - Dungeon Master Edition")
    print("=" * 60)
    print("\nInitializing AI Dungeon Master...")
    
    # Initialize the model
    model = create_client()
    
    # Start a chat session
    chat = model.start_chat(history=[])
    
    # Get the opening narration from the DM
    print("\n" + "-" * 60)
    opening = get_dm_response(chat, "Begin the adventure. Welcome me as a new player and set the scene.")
    print(f"\n🎲 Dungeon Master:\n{opening}")
    
    print("\n" + "-" * 60)
    print("Commands: Type your action, 'quit' to exit")
    print("-" * 60)
    
    # Main game loop
    while True:
        # Get player input
        print()
        player_input = input("⚔️  Your action: ").strip()
        
        # Check for exit commands
        if player_input.lower() in ["quit", "exit", "q"]:
            print("\n🎲 Dungeon Master: Your adventure ends here... for now.")
            print("Thanks for playing! See you next time, adventurer.")
            break
        
        # Skip empty input
        if not player_input:
            print("(Please enter an action or 'quit' to exit)")
            continue
        
        # Get DM response
        print("\n🎲 Dungeon Master:")
        response = get_dm_response(chat, player_input)
        print(response)


if __name__ == "__main__":
    main()
