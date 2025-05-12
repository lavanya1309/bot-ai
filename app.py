from flask import Flask, render_template, request, jsonify
import requests
import re
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Groq AI API configuration
GROQ_API_KEY = "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"  # Get at console.groq.com
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-70b-8192"

# Store conversation history
conversation_history = []

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

@app.route('/')
def index():
    formatted_history = []
    for item in conversation_history:
        formatted_query = markdown.markdown(item['query'])
        formatted_response = format_code_blocks(markdown.markdown(item['response']))
        formatted_history.append({'query': formatted_query, 'response': formatted_response})
    return render_template('index.html', conversation=formatted_history)

@app.route('/ask', methods=['POST'])
def ask():
    query = request.form['query']
    if not query.strip():
        return jsonify({'error': 'Please enter a question'})

    try:
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. When providing code, always enclose it in markdown code blocks (using ```). After the code block, provide a clear and concise explanation of the code."},
            *[{"role": "user" if i % 2 == 0 else "assistant", "content": msg['query'] if i % 2 == 0 else msg['response']}
              for i, msg in enumerate(conversation_history[-3:])],
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

        reply = result['choices'][0]['message']['content']

        # Store the conversation
        conversation_history.append({'query': query, 'response': reply})

        # Format the response
        formatted_reply = format_code_blocks(markdown.markdown(reply))

        return jsonify({'response': formatted_reply})

    except requests.exceptions.RequestException as e:
        return jsonify({'error': f"API request failed: {str(e)}"})
    except Exception as e:
        return jsonify({'error': f"An error occurred: {str(e)}"})

@app.route('/new_chat', methods=['POST'])
def new_chat():
    conversation_history.clear()
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
