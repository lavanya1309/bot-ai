# app.py
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
GROQ_API_KEY = "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"  # Replace with your actual Groq API key
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-70b-8192"

# Directory to store chat history
CHAT_HISTORY_DIR = "chat_history.json"
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
        messages = [
            {"role": "system", "content": """You are a highly skilled AI assistant that excels at providing information in structured formats. When the user asks for a comparison or the difference between two or more items, you MUST present the information as a Markdown table.

For example, if the user asks "What is the difference between X and Y?", your response should look like this:

| Feature | X | Y |
|---|---|---|
| Feature 1 | Description of X's Feature 1 | Description of Y's Feature 1 |
| Feature 2 | Description of X's Feature 2 | Description of Y's Feature 2 |
| ... | ... | ... |

Specifically, when asked for the difference between AWS and Azure cloud services, provide a detailed comparison in the following Markdown table format:

| Category | AWS Service | Azure Service |
|---|---|---|
| Compute | EC2 | Virtual Machines |
| Container Service | ECS, EKS | Azure Container Service (ACS), AKS |
| Serverless | Lambda | Azure Functions |
| Database (Relational) | RDS | Azure Database for MySQL/PostgreSQL/SQL Server |
| Database (NoSQL) | DynamoDB | Azure Cosmos DB |
| Storage (Object) | S3 | Blob Storage |
| Storage (Block) | EBS | Azure Disk Storage |
| Identity Management | IAM | Azure Active Directory (AAD) |
| Network | VPC | Azure Virtual Network (VNet) |
| AI/ML | SageMaker | Azure Machine Learning |
| ... | ... | ... |

For other types of questions that do not involve comparison, follow the previous instructions for code blocks and explanations."""},
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
        print(f"Groq Response: {result}")

        reply = result['choices'][0]['message']['content']

        current_conversation.append({'query': query, 'response': reply})

        formatted_reply = format_code_blocks(markdown.markdown(reply))
        print(f"Flask Response: {jsonify({'response': formatted_reply, 'is_error': False})}")

        return jsonify({'response': formatted_reply, 'is_error': False})

    except requests.exceptions.RequestException as e:
        error_message = f"API request failed: {str(e)}"
        print(f"Flask Error (RequestException): {error_message}")
        return jsonify({'error': error_message, 'is_error': True})
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(f"Flask Error (General): {error_message}")
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
