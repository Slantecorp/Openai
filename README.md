# Slack AI Assistant with Memory Management

This repository contains a Slack bot built with [Slack Bolt](https://slack.dev/bolt-python/), Flask, and OpenAI's GPT-4 API. The bot uses a SQLite database to manage per-user memories, conversation history, and can retrieve instructional files from a network drive to help guide users through tasks.

## Features

- **Memory Management:**  
  - Save memories with the `!remember <text>` command.
  - List stored memories with `!listmemories`.
  - Delete a memory by its ID using `!deletememory <id>`.
- **Conversation History Logging:**  
  - Logs all messages (both user and assistant) per user.
  - View the conversation history with `!showhistory`.
- **Instruction Retrieval:**  
  - Use the `!howto <task>` command to retrieve instructions for a task from a file on a network drive.
- **OpenAI Integration:**  
  - Uses stored memories as context when generating AI responses.
- **Slack Integration:**  
  - Built using Slack Bolt and Flask to serve as a public endpoint for Slack events (e.g., using [ngrok](https://ngrok.com/) in development).

## Prerequisites

- Python 3.7 or higher
- Slack App with the following credentials:
  - Bot Token (`SLACK_BOT_TOKEN`)
  - Signing Secret (`SLACK_SIGNING_SECRET`)
- (For development) [ngrok](https://ngrok.com/) to expose your local Flask server to the internet.
- SQLite (included with Python)

## Installation

### 1. Clone the Repository:

```bash
git clone https://github.com/Sgt.Dicks/openai.git
cd openai
```

### 2. Create a Virtual Environment (optional but recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install the Required Dependencies:

```bash
pip install -r requirements.txt
```

_(Make sure your `requirements.txt` includes packages like `slack_bolt`, `flask`, `python-dotenv`, and `openai`.)_

### 4. Set Up Environment Variables:

Create a `.env` file in the project root with the following content:

```ini
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your-slack-signing-secret
PORT=3000
```

### 5. Set Up the SQLite Database:

Create the SQLite database file (`memories.db`) with the following schema. You can use your preferred SQLite client or run these commands in a script:

```sql
-- Table for storing the OpenAI API key:
CREATE TABLE IF NOT EXISTS api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    service TEXT UNIQUE NOT NULL,
    api_key TEXT NOT NULL
);

-- Table for storing memories (each with a username):
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    memory_text TEXT NOT NULL,
    category TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table for logging conversation history:
CREATE TABLE IF NOT EXISTS conversation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    role TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 6. Insert Your OpenAI API Key:

```sql
INSERT INTO api_keys (service, api_key) VALUES ('openai', 'your_openai_api_key_here');
```

### 7. Configure Your Network Drive (NOT FULLY IMPLAMENTED):

If you plan to use the `!howto <task>` command, ensure your network drive is mounted (e.g., as `Z:/instructions/`) or adjust the file path in the code accordingly.

## Usage

### 1. Expose Your Local Endpoint (Development):

If you are running the bot locally, use `ngrok` to expose your Flask server:

```bash
ngrok http 3000
```

Copy the public HTTPS URL provided by `ngrok` (e.g., `https://abcdef1234.ngrok.io`) and set it as the **Request URL** in your Slack App’s Event Subscriptions (append `/slack/events`).

### 2. Run the Application:

```bash
python SQL Test.py
```

### 3. Interact with Your Bot in Slack:

Invite your bot to a channel or send it a direct message.  
Use commands:

- `!help` — To see available commands.
- `!remember my favorite color is red` — To save a memory.
- `!listmemories` — To list your stored memories.
- `!deletememory 1` — To delete a memory by its ID.
- `!showhistory` — To display your conversation history.
- `!howto <task>` — To retrieve instructions for a task.
