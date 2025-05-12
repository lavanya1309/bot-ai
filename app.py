from flask import Flask, render_template, request
import requests

app = Flask(__name__)

GEMINI_API_KEY = "AIzaSyCFU2WJ3G2Szis2xdII2krXONqa0pM_iik"
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    query = request.form['query']
    try:
        headers = {'Content-Type': 'application/json'}
        prompt = f"""
Answer the following in clear step-by-step format.
Use:
Step 1:
<command>
Step 2:
<command>
Do NOT use any extra explanation or HTML or **bold text** or code blocks.
Just list steps one after another.
User question: {query}
"""
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        response = requests.post(GEMINI_URL, headers=headers, json=data)
        result = response.json()
        reply = result['candidates'][0]['content']['parts'][0]['text']

        # Convert plain text with \n into HTML <br> for rendering
        reply = reply.replace('\n', '<br>')

    except Exception as e:
        reply = f"⚠️ Error: {str(e)}"
    return render_template('index.html', query=query, response=reply)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
