from flask import Flask, render_template, request
import requests
import re

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

        # Modify the prompt to ask the AI for a more conversational, natural response
        prompt = f"""
        Answer the following question in a conversational format. Provide relevant and clear information, 
        but avoid step-by-step instructions unless it's absolutely necessary. If you mention commands or code, 
        highlight them clearly in the response.
        
        User question: {query}
        """
        
        # Prepare the data for the API request
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }

        # Make the API request
        response = requests.post(GEMINI_URL, headers=headers, json=data)
        result = response.json()

        # Extract the reply from the response
        reply = result['candidates'][0]['content']['parts'][0]['text']

        # Clean up unwanted HTML tags or line breaks
        reply = reply.replace('<br>', '\n')  # Replace <br> tags with newline
        reply = reply.strip()  # Remove leading/trailing whitespace

        # Remove any additional HTML tags (like <p>, <div>, etc.)
        reply = reply.replace('<p>', '').replace('</p>', '')
        reply = reply.replace('<div>', '').replace('</div>', '')

        # Detect commands and highlight them with bold markers
        reply = re.sub(r'(sudo|apt|systemctl|curl|git|mkdir|\b\d+\b)', r'<b>\1</b>', reply)

        # If the response is too brief or empty, provide a default message
        if not reply or len(reply.splitlines()) < 3:
            reply = "⚠️ Sorry, I wasn't able to get a detailed response. Here's a basic guide:\n\nStep 1: Run 'sudo apt update'\nStep 2: Run 'sudo apt install nginx'\nStep 3: Run 'sudo systemctl start nginx'\nStep 4: Run 'sudo systemctl enable nginx'\nStep 5: Run 'sudo systemctl status nginx'"

    except Exception as e:
        reply = f"⚠️ Error: {str(e)}"
    
    # Return the response to the template
    return render_template('index.html', query=query, response=reply)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
