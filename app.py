from flask import Flask, render_template, request, jsonify
import requests
import re
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Groq AI API configuration
GROQ_API_KEY = "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"
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
            timestamp_str = filename[5:-5]
            chat_time = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            if chat_time >= one_day_ago:
                history = load_chat_history(filename)
                if history:
                    summary = history[0]['query'][:50] + "..." if len(history[0]['query']) > 50 else history[0]['query']
                    last_day_chats.append({'filename': filename, 'summary': summary, 'timestamp': chat_time.strftime("%H:%M")})
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

def format_tables(text):
    # Fix tables without proper spacing (e.g., "FeatureDockerKubernetes")
    text = re.sub(
        r'([a-zA-Z])([A-Z][a-z]+)([A-Z][a-z]+)',
        r'\1 | \2 | \3 |',
        text
    )
    
    # Convert to proper Markdown table format
    text = re.sub(
        r'([^|]+)\|([^|]+)\|([^|]+)\|',
        lambda m: f"| {m.group(1).strip()} | {m.group(2).strip()} | {m.group(3).strip()} |\n",
        text
    )
    
    # Add header separator if missing
    if "|---" not in text:
        text = re.sub(
            r'(\|.*\|.*\n)',
            r'\1|:---|:---|:---|\n',
            text,
            count=1
        )
    
    # Convert Markdown to HTML
    text = markdown.markdown(text, extensions=['tables'])
    
    # Add table container and styling
    text = re.sub(
        r'<table>',
        '<div class="table-container"><table class="comparison-table">',
        text
    )
    text = re.sub(r'</table>', '</table></div>', text)
    
    return text

@app.route('/get_last_day_chats', methods=['GET'])
def get_last_day_chats_ajax():
    chats = get_last_day_chats()
    return jsonify(chats)

@app.route('/delete_chat', methods=['POST'])
def delete_chat():
    filename = request.form['filename']
    filepath = os.path.join(CHAT_HISTORY_DIR, filename)
    try:
        os.remove(filepath)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    previous_chats = get_last_day_chats()
    formatted_history = []
    for item in current_conversation:
        formatted_query = markdown.markdown(item['query'])
        formatted_response = markdown.markdown(item['response'])
        formatted_response = format_code_blocks(formatted_response)
        formatted_response = format_tables(formatted_response)
        formatted_history.append({'query': formatted_query, 'response': formatted_response})
    return render_template('index.html', conversation=formatted_history, previous_chats=previous_chats)

@app.route('/ask', methods=['POST'])
def ask():
    query = request.form['query']
    if not query.strip():
        return jsonify({'error': 'Please enter a question'})
    
    system_prompt = """When comparing services, provide a Markdown table with:
1. Clear headers in first row
2. Alignment markers in second row (|:---|:---:|)
3. Concise but informative content
4. All major comparison points"""

    messages = [
        {"role": "system", "content": system_prompt},
        *[{"role": "user" if i % 2 == 0 else "assistant", "content": msg['query'] if i % 2 == 0 else msg['response']}
          for i, msg in enumerate(current_conversation[-3:])],
        {"role": "user", "content": query}
    ]

    try:
        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": messages,
                "temperature": 0.7
            }
        )
        response.raise_for_status()
        reply = response.json()['choices'][0]['message']['content']
        
        current_conversation.append({'query': query, 'response': reply})
        
        formatted_reply = markdown.markdown(reply)
        formatted_reply = format_code_blocks(formatted_reply)
        formatted_reply = format_tables(formatted_reply)
        
        return jsonify({'response': formatted_reply})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
            formatted_response = markdown.markdown(item['response'])
            formatted_response = format_code_blocks(formatted_response)
            formatted_response = format_tables(formatted_response)
            formatted_history.append({'query': formatted_query, 'response': formatted_response})
        return jsonify({'success': True, 'conversation': formatted_history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
