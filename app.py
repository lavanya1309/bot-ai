from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
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

# Gemini AI API configuration
GEMINI_API_KEY = "AIzaSyCriLYjFnFwJ8rzjG7r358Ef_7ENsP-jLc"  # Replace with your actual Gemini API key
MODEL_NAME = "models/gemini-1.5-pro-latest"  # ✅ Fixed model name

# Initialize Gemini API
genai.configure(api_key=GEMINI_API_KEY)
generation_config = genai.GenerationConfig(temperature=0.7)
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
]

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
                else:
                    break
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

@app.route('/delete_chat', methods=['POST'])
def delete_chat():
    filename = request.form['filename']
    filepath = os.path.join(CHAT_HISTORY_DIR, filename)
    try:
        os.remove(filepath)
        return jsonify({'success': True})
    except FileNotFoundError:
        return jsonify({'error': 'Chat history not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Error deleting chat: {str(e)}'}), 500

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
        return jsonify({'error': 'Please enter a question', 'is_error': True})
    try:
        contents = []
        for msg in [
            {"role": "system", "content": """You are a helpful AI assistant. When the user asks for a comparison, present the information in a Markdown table."""},
            *[{"role": "user" if i % 2 == 0 else "assistant", "content": msg['query'] if i % 2 == 0 else msg['response']}
              for i, msg in enumerate(current_conversation[-3:])],
            {"role": "user", "content": query}
        ]:
            contents.append({
                "role": msg["role"],
                "parts": [{"text": msg["content"]}]
            })

        model = genai.GenerativeModel(MODEL_NAME)
        response = model.generate_content(contents=contents)
        reply = response.text

        current_conversation.append({'query': query, 'response': reply})
        formatted_reply = format_code_blocks(markdown.markdown(reply))
        return jsonify({'response': formatted_reply, 'is_error': False})

    except Exception as e:
        error_message = f"An error occurred with the Gemini API: {str(e)}"
        print(f"Flask Error (Gemini API): {error_message}")
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

# ✅ Optional route to list available models
@app.route('/list_models')
def list_models():
    try:
        models = list(genai.list_models())
        for model_info in models:
            print(model_info.name)
        return "Available models listed in console"
    except Exception as e:
        return f"Error listing models: {e}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
