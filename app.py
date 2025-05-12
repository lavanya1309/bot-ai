from flask import Flask, render_template, request, jsonify
import requests
import re
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

GEMINI_API_KEY = "AIzaSyCFU2WJ3GzSzis2xdII2krXONqa0pM_iik"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

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
        # Include conversation history in the prompt
        history_context = "\n".join([f"User: {item['query']}\nAI: {item['response']}" 
                                   for item in conversation_history[-3:]])
        
        prompt = f"""
        You are an AI assistant similar to DeepSeek. Provide detailed, well-structured answers with:
        - Clear explanations
        - Proper formatting (headings, lists, code blocks)
        - Examples when applicable
        - Error solutions if the user mentions an error
        
        Previous conversation:
        {history_context}
        
        New question: {query}
        """
        
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.9,
                "maxOutputTokens": 2000
            }
        }

        response = requests.post(GEMINI_URL, headers={'Content-Type': 'application/json'}, json=data)
        response.raise_for_status()
        result = response.json()

        if 'candidates' not in result or not result['candidates']:
            raise ValueError("No valid response from the AI model")

        reply = result['candidates'][0]['content']['parts'][0]['text']
        
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
    except ValueError as e:
        error_msg = f"API error: {str(e)}"
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
