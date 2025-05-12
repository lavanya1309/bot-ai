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

# ... [keep your existing format_code_blocks and route functions] ...

@app.route('/ask', methods=['POST'])
def ask():
    query = request.form['query']
    if not query.strip():
        return jsonify({'error': 'Please enter a question'})
    
    try:
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

        response = requests.post(GROQ_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()

        reply = result['choices'][0]['message']['content']
        
        # Format and return response (same as before)
        # ... [rest of your existing code]

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
