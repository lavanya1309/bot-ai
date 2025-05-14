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
    """
    Convert markdown to HTML and highlight code blocks using Pygments
    """
    # Convert markdown to HTML
    html = markdown.markdown(text)
    
    # Process code blocks with Pygments
    def replacer(match):
        language = match.group(1) or 'text'
        code = match.group(2)
        
        try:
            lexer = get_lexer_by_name(language, stripall=True)
            formatter = HtmlFormatter(style='friendly')
            return highlight(code, lexer, formatter)
        except:
            return f'<pre><code>{code}</code></pre>'
    
    # This pattern matches both ```lang and ``` code blocks
    html = re.sub(r'```(\w*)\n(.*?)\n```', replacer, html, flags=re.DOTALL)
    
    return html

@app.route('/')
def home():
    """Render the main chat interface"""
    return render_template('index.html', conversation=conversation_history)

@app.route('/ask', methods=['POST'])
def ask():
    """Handle AI queries"""
    query = request.form['query']
    if not query.strip():
        return jsonify({'error': 'Please enter a question'})
    
    try:
        # Prepare messages with conversation history (last 3 exchanges)
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
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

        # Make API request to Groq
        response = requests.post(GROQ_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        reply = result['choices'][0]['message']['content']
        
        # Store the conversation
        conversation_history.append({'query': query, 'response': reply})
        
        # Format the response with code highlighting
        formatted_reply = format_code_blocks(reply)
        
        return jsonify({'response': formatted_reply})
    
    except requests.exceptions.RequestException as e:
        return jsonify({'error': f"API request failed: {str(e)}"})
    except Exception as e:
        return jsonify({'error': f"An error occurred: {str(e)}"})

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return app.send_static_file(path)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
