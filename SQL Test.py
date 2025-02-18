import os
import re
import openai
import sqlite3
from flask import Flask, request, jsonify
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Database File ---
DB_FILE = "memories.db"

# --- Database Functions ---

def get_api_key():
    """Retrieve the OpenAI API key from the database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT api_key FROM api_keys WHERE service = 'openai'")
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        else:
            raise ValueError("No OpenAI API key found in the database.")
    except Exception as e:
        print("Error retrieving API key:", e)
        return None

def fetch_memory_from_db(username):
    """Fetch all stored memories for the specified username from the database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        query = "SELECT id, memory_text FROM memories WHERE username = ?"
        cursor.execute(query, (username,))
        results = cursor.fetchall()
        conn.close()
        if results:
            # Format each memory with its ID
            memory_texts = "\n".join([f"{row[0]}: {row[1]}" for row in results])
            print(f"Memories retrieved for {username}:\n", memory_texts)
            return memory_texts
        else:
            print(f"No memories found for {username}.")
            return "No stored memories available."
    except Exception as e:
        print("SQL Error:", e)
        return "Memory lookup failed."


def save_memory_to_db(memory_text, username, category=None):
    """Save a new memory into the database (with the username)."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        if category:
            cursor.execute(
                "INSERT INTO memories (username, memory_text, category) VALUES (?, ?, ?)",
                (username, memory_text, category)
            )
        else:
            cursor.execute(
                "INSERT INTO memories (username, memory_text) VALUES (?, ?)",
                (username, memory_text)
            )
        conn.commit()
        conn.close()
        print(f"Memory saved for {username}: {memory_text}")
        return "✅ I have remembered that."
    except Exception as e:
        print("Error saving memory:", e)
        return "❌ I couldn't save that memory."

def delete_memory_by_id(memory_id):
    """Delete a memory from the database by its ID."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
        conn.close()
        return f"✅ Memory {memory_id} deleted."
    except Exception as e:
        print("Error deleting memory:", e)
        return "❌ Failed to delete memory."

def log_conversation(username, role, message):
    """Log each conversation message (from user or assistant) into the database."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversation_history (username, role, message) VALUES (?, ?, ?)",
            (username, role, message)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print("Error logging conversation:", e)

def fetch_conversation_history(username):
    """Retrieve the conversation history for a given username."""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        query = """
            SELECT role, message, created_at 
            FROM conversation_history 
            WHERE username = ? 
            ORDER BY created_at ASC
        """
        cursor.execute(query, (username,))
        results = cursor.fetchall()
        conn.close()
        if results:
            history = "\n".join([f"{row[2]} - {row[0]}: {row[1]}" for row in results])
            return history
        else:
            return "No conversation history found."
    except Exception as e:
        print("Error fetching conversation history:", e)
        return "Failed to fetch conversation history."

# --- Command Processing ---

def process_command(user_input, username):
    """
    Process special commands that start with an exclamation point.
    Available commands:
      !help - Show help text.
      !remember <text> - Save a new memory.
      !listmemories - List all stored memories.
      !deletememory <id> - Delete a memory by its ID.
      !showhistory - Show conversation history.
    """
    command = user_input.strip().lower()
    if command.startswith("!help"):
        return (
            "Available commands:\n"
            "!help - Show this help message\n"
            "!remember <memory> - Save a new memory\n"
            "!listmemories - List all stored memories\n"
            "!deletememory <id> - Delete a memory by its ID\n"
            "!showhistory - Show conversation history\n"
        )
    elif command.startswith("!remember"):
        memory_text = user_input[len("!remember"):].strip(": ").strip()
        if not memory_text:
            return "Usage: !remember <memory text>"
        result = save_memory_to_db(memory_text, username)
        log_conversation(username, "system", f"Saved memory: {memory_text}")
        return result
    elif command.startswith("!listmemories"):
        memories = fetch_memory_from_db(username)
        return "Memories:\n" + memories
    elif command.startswith("!deletememory"):
        parts = user_input.strip().split()
        if len(parts) < 2:
            return "Usage: !deletememory <id>"
        try:
            memory_id = int(parts[1])
        except ValueError:
            return "Invalid memory ID. Usage: !deletememory <id>"
        result = delete_memory_by_id(memory_id)
        return result
    elif command.startswith("!showhistory"):
        history = fetch_conversation_history(username)
        return "Conversation History:\n" + history
    else:
        return "Unknown command. Type !help for a list of commands."

# --- AI Interaction ---

def get_ai_response(user_input, username):
    """Get an AI-generated response from OpenAI using the user's stored memories as context."""
    openai_api_key = get_api_key()
    if not openai_api_key:
        return "❌ Error: OpenAI API key not found."
    
    client = openai.OpenAI(api_key=openai_api_key)
    
    # Retrieve only the memories for this specific user.
    memory_context = fetch_memory_from_db(username)
    system_message = f"Here are your memories: {memory_context}"
    print("\nSystem Content Being Sent to OpenAI:\n", system_message, "\n")
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_input}
        ],
        temperature=0.7,
        max_tokens=200
    )
    ai_message = response.choices[0].message.content
    log_conversation(username, "assistant", ai_message)
    return ai_message

# --- Slack Bolt App Setup with Flask ---

# Retrieve Slack tokens from environment variables
SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")
SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")

# Initialize the Slack Bolt app
bolt_app = App(token=SLACK_BOT_TOKEN, signing_secret=SLACK_SIGNING_SECRET)
# Create a SlackRequestHandler for Flask integration
handler = SlackRequestHandler(bolt_app)

# Define the event handler for messages
@bolt_app.message("")
def handle_message_events(message, say):
    text = message.get("text", "")
    user_id = message.get("user", "unknown")
    # Now, all commands and responses will be associated with this user.
    if text.strip().startswith("!"):
        response_text = process_command(text, user_id)
        log_conversation(user_id, "system", f"Executed command: {text}")
    else:
        log_conversation(user_id, "user", text)
        response_text = get_ai_response(text, user_id)
    say(response_text)
    
# Set up the Flask app to serve as the HTTP endpoint for Slack events.
flask_app = Flask(__name__)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)

# --- Main: Run the Flask Server ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    flask_app.run(host="0.0.0.0", port=port)
