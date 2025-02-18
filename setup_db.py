import sqlite3

DB_FILE = "memories.db"

def setup_database():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Create the memories table (with an optional category column)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                memory_text TEXT NOT NULL,
                category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Create the api_keys table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT UNIQUE NOT NULL,
                api_key TEXT NOT NULL
            );
        """)

        # Create the conversation_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                role TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Optionally, insert the OpenAI API key if not already stored
        cursor.execute("SELECT COUNT(*) FROM api_keys WHERE service = 'openai'")
        count = cursor.fetchone()[0]
        if count == 0:
            # Replace with your actual key.
            cursor.execute("INSERT INTO api_keys (service, api_key) VALUES (?, ?)", 
                           ("openai", "your_actual_openai_api_key_here"))
            print("Inserted OpenAI API Key into the database.")

        conn.commit()
        conn.close()
        print("✅ Database setup complete.")
    except Exception as e:
        print("❌ Error setting up database:", e)

if __name__ == "__main__":
    setup_database()
