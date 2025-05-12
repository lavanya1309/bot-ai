from flask import Flask, render_template, request, jsonify
import requests
import re
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Free AI API configuration (OpenRouter)
OPENROUTER_API_KEY = "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"  # Replace with your key
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "gryphe/mythomax-l2-13b"  # Free model (or try 'meta-llama/llama-3-70b-instruct')

# Store conversation history
conversation_history = []

def format_code_blocks(text):
    """Format code blocks with syntax highlighting"""
    pattern = r'```(\w+)?\n([\s\S]+?)\n```'
    
    def replacer(match):
        language = match.group(1) or 'text'
        code = match.group(2)
        
        try:
            lexer = get_lexer_by_name(language, stripall=True)
            formatter = HtmlFormatter(style='colorful', cssclass='codehilite')
            return highlight(code, lexer, formatter)
        except:
            return f'<pre><code>{code}</code></pre>'
    
    return re.sub(pattern, replacer, text)

@app.route('/')
def home():
    return render_template('index.html', conversation=conversation_history)

@app.route('/ask', methods=['POST'])
def ask():
    query = request.form['query']
    if not query.strip():
        return jsonify({'error': 'Please enter a question'})
    
    try:
        # Prepare messages with conversation history
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            *[{"role": "user" if i % 2 == 0 else "assistant", "content": msg['query'] if i % 2 == 0 else msg['response']} 
              for i, msg in enumerate(conversation_history[-3:])],
            {"role": "user", "content": query}
        ]

        data = {
            "model": MODEL,
            "messages": messages,
            "temperature": 0.7
        }

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "http://localhost:5000",  # Your website URL
            "X-Title": "AI Assistant"  # Your app name
        }

        response = requests.post(OPENROUTER_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        reply = result['choices'][0]['message']['content']
        
        # Format the response
        reply = format_code_blocks(reply)
        reply = markdown.markdown(reply, extensions=['fenced_code', 'tables'])
        
        # Add to conversation history
        conversation_history.append({
            'query': query,
            'response': reply,
            'is_error': False
        })
        
        return jsonify({
            'query': query,
            'response': reply,
            'is_error': False
        })

    except requests.exceptions.RequestException as e:
        error_msg = f"Network error: {str(e)}"
        if hasattr(e, 'response') and e.response:
            try:
                error_details = e.response.json()
                error_msg += f"\nDetails: {error_details.get('error', {}).get('message', 'No details')}"
            except:
                error_msg += f"\nStatus: {e.response.status_code}"
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
    
    # Add error to conversation history
    conversation_history.append({
        'query': query,
        'response': error_msg,
        'is_error': True
    })
    
    return jsonify({
        'query': query,
        'response': error_msg,
        'is_error': True
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
