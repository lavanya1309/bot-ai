from flask import Flask, render_template, request, jsonify
import requests
import re
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from datetime import datetime, timedelta
import json  # For saving/loading chat history
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Groq AI API configuration
GROQ_API_KEY = "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"  # Get at console.groq.com
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-70b-8192"

# Directory to store chat history
CHAT_HISTORY_DIR = "chat_history"
os.makedirs(CHAT_HISTORY_DIR, exist_ok=True)

# Store the current conversation
current_conversation = []

def save_chat_history(history):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(CHAT_HISTORY_DIR, f"chat_{timestamp}.json")
    with open(filename, 'w') as f:
        json.dump(history, f)

def load_chat_history(filename):
    filepath = os.path.join(CHAT_HISTORY_DIR, filename)
    with open(filepath, 'r') as f:
        return json.load(f)

def get_last_day_chats():
    now = datetime.now()
    one_day_ago = now - timedelta(days=1)
    chat_files = [f for f in os.listdir(CHAT_HISTORY_DIR) if f.startswith("chat_") and f.endswith(".json")]
    last_day_chats = []
    for filename in sorted(chat_files, reverse=True):
        try:
            timestamp_str = filename[5:-5]  # Extract timestamp from filename
            chat_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            if chat_time >= one_day_ago:
                # Load a summary (e.g., the first query) for display
                history = load_chat_history(filename)
                if history:
                    summary = history[0]['query'][:50] + "..." if len(history[0]['query']) > 50 else history[0]['query']
                    last_day_chats.append({'filename': filename, 'summary': summary, 'timestamp': chat_time.strftime("%H:%M")})
            else:
                break  # Since files are sorted by time, we can stop
        except ValueError:
            continue
    return last_day_chats

def format_code_blocks(text):
    def replace(match):
        code = match.group(2)
        language = match.group(1) if match.group(1) else 'python'
        try:
            lexer = get_lexer_by_name(language)
        except:
            lexer = get_lexer_by_name('text')
        formatter = HtmlFormatter(style='monokai')
        highlighted_code = highlight(code, lexer, formatter)
        return f'<div class="code-block"><pre><code class="{language}">{highlighted_code}</code></pre></div>'

    pattern = re.compile(r'```(\w+)?\n(.*?)\n```', re.DOTALL)
    return re.sub(pattern, replace, text)

@app.route('/get_last_day_chats', methods=['GET'])
def get_last_day_chats_ajax():
    chats = get_last_day_chats()
    return jsonify(chats)

@app.route('/')
def index():
    previous_chats = get_last_day_chats()
    formatted_history = []
    for item in current_conversation:
        formatted_query = markdown.markdown(item['query'])
        formatted_response = format_code_blocks(markdown.markdown(item['response']))
        formatted_history.append({'query': formatted_query, 'response': formatted_response})
    return render_template('index.html', conversation=formatted_history, previous_chats=previous_chats)

@app.route('/ask', methods=['POST'])
def ask():
    query = request.form['query']
    if not query.strip():
        return jsonify({'error': 'Please enter a question'})

    try:
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Your goal is to understand the user's questions and provide clear, concise, and easy-to-understand answers. When providing code, always enclose it in markdown code blocks (using ```) and follow it with a step-by-step explanation of what the code does. Use analogies or real-world examples whenever possible to clarify complex concepts. Tailor your explanations to be accessible to a general audience."},
            *[{"role": "user" if i % 2 == 0 else "assistant", "content": msg['query'] if i % 2 == 0 else msg['response']}
              for i, msg in enumerate(current_conversation[-3:])],
            {"role": "user", "content": query}
        ]

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": MODEL,
            "messages": messages,
            "temperature": 0.7
        }

        response = requests.post(GROQ_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        print(f"Groq Response: {result}")  # Debugging

        reply = result['choices'][0]['message']['content']

        # Store the current conversation turn
        current_conversation.append({'query': query, 'response': reply})

        # Format the response
        formatted_reply = format_code_blocks(markdown.markdown(reply))
        print(f"Flask Response: {jsonify({'response': formatted_reply})}") # Debugging

        return jsonify({'response': formatted_reply, 'is_error': False}) # Ensure is_error is always included

    except requests.exceptions.RequestException as e:
        error_message = f"API request failed: {str(e)}"
        print(f"Flask Error (RequestException): {error_message}") # Debugging
        return jsonify({'error': error_message, 'is_error': True})
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(f"Flask Error (General): {error_message}") # Debugging
        return jsonify({'error': error_message, 'is_error': True})

@app.route('/new_chat', methods=['POST'])
def new_chat():
    global current_conversation
    if current_conversation:
        save_chat_history(current_conversation)
    current_conversation = []
    return jsonify({'success': True})

@app.route('/load_chat', methods=['POST'])
def load_chat():
    filename = request.form['filename']
    try:
        global current_conversation
        current_conversation = load_chat_history(filename)
        formatted_history = []
        for item in current_conversation:
            formatted_query = markdown.markdown(item['query'])
            formatted_response = format_code_blocks(markdown.markdown(item['response']))
            formatted_history.append({'query': formatted_query, 'response': formatted_response})
        return jsonify({'success': True, 'conversation': formatted_history})
    except FileNotFoundError:
        return jsonify({'error': 'Chat history not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Error loading chat: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
