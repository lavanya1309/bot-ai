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
        prompt = f"""Explain this in clear simple steps using 'Step 1:', 'Step 2:' format. If there are any commands, just display them on a new line, without backticks or code blocks. Question: {query}"""
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        response = requests.post(GEMINI_URL, headers=headers, json=data)
        result = response.json()
        reply = result['candidates'][0]['content']['parts'][0]['text']

        # Format line breaks for HTML display
        reply = reply.replace('\n', '<br>')

    except Exception as e:
        reply = f"⚠️ Error: {str(e)}"
    return render_template('index.html', query=query, response=reply)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
