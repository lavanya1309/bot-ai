from flask import Flask, render_template, request
import requests
import os

app = Flask(__name__)

# Replace with your actual Gemini API key
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
        data = {
            "contents": [{
                "parts": [{"text": query}]
            }]
        }
        response = requests.post(GEMINI_URL, headers=headers, json=data)
        result = response.json()
        reply = result['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        reply = f"⚠️ Error: {str(e)}"
    return render_template('index.html', query=query, response=reply)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
