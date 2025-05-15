from flask import Flask, render_template, request, jsonify, send_file
import requests
import re
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from datetime import datetime, timedelta
import json
import os
from docx import Document
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Groq AI API configuration
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama3-70b-8192"

# Directory to store chat history
CHAT_HISTORY_DIR = "chat_history"
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
                    last_day_chats.append({
                        'filename': filename,
                        'summary': summary,
                        'timestamp': chat_time.strftime("%H:%M")
                    })
        except ValueError:
            continue
    return last_day_chats

def format_code_blocks(text):
    def replace(match):
        language = match.group(1) or 'python'
        code = match.group(2)
        try:
            lexer = get_lexer_by_name(language)
        except:
            lexer = get_lexer_by_name('text')
        formatter = HtmlFormatter(style='monokai')
        highlighted_code = highlight(code, lexer, formatter)
        return f'<div class="code-block"><pre><code class="{language}">{highlighted_code}</code></pre></div>'
    
    pattern = re.compile(r'```(\w+)?\n(.*?)\n```', re.DOTALL)
    return re.sub(pattern, replace, text)

def format_tables(text):
    text = re.sub(r'\|\s*\|\s*\|', '| --- | --- |', text)

    def process_table(match):
        rows = [row.strip() for row in match.group(0).split('\n') if row.strip() and '---' not in row]
        if len(rows) < 2:
            return match.group(0)

        headers = [h.strip() for h in rows[0].split('|') if h.strip()]
        html = '<div class="table-container"><table class="comparison-table"><thead><tr>'
        html += ''.join(f'<th>{header}</th>' for header in headers) + '</tr></thead><tbody>'

        for row in rows[1:]:
            cells = [c.strip() for c in row.split('|') if c.strip()]
            if len(cells) == len(headers):
                html += '<tr>' + ''.join(f'<td>{cell}</td>' for cell in cells) + '</tr>'

        html += '</tbody></table></div>'
        return html

    text = re.sub(r'(\|.*\|.*\n)(\|.*\|\n)*', process_table, text)
    return text

def generate_word_document(content):
    doc = Document()
    doc.add_heading('Generated Document', 0)
    
    # Remove markdown formatting
    plain_text = re.sub(r'#+\s*', '', content)  # Remove headings
    plain_text = re.sub(r'\*\*(.*?)\*\*', r'\1', plain_text)  # Remove bold
    plain_text = re.sub(r'\*(.*?)\*', r'\1', plain_text)  # Remove italics
    plain_text = re.sub(r'`(.*?)`', r'\1', plain_text)  # Remove code
    plain_text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', plain_text)  # Remove links
    
    for paragraph in plain_text.split('\n'):
        if paragraph.strip():
            doc.add_paragraph(paragraph)
    
    file_stream = BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream

def generate_pdf_document(content):
    file_stream = BytesIO()
    doc = SimpleDocTemplate(file_stream, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Remove markdown formatting
    plain_text = re.sub(r'#+\s*', '', content)
    plain_text = re.sub(r'\*\*(.*?)\*\*', r'\1', plain_text)
    plain_text = re.sub(r'\*(.*?)\*', r'\1', plain_text)
    plain_text = re.sub(r'`(.*?)`', r'\1', plain_text)
    plain_text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', plain_text)
    
    story = []
    for paragraph in plain_text.split('\n'):
        if paragraph.strip():
            story.append(Paragraph(paragraph, styles["Normal"]))
    
    doc.build(story)
    file_stream.seek(0)
    return file_stream

def generate_txt_document(content):
    # Remove markdown formatting
    plain_text = re.sub(r'#+\s*', '', content)
    plain_text = re.sub(r'\*\*(.*?)\*\*', r'\1', plain_text)
    plain_text = re.sub(r'\*(.*?)\*', r'\1', plain_text)
    plain_text = re.sub(r'`(.*?)`', r'\1', plain_text)
    plain_text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', plain_text)
    
    file_stream = BytesIO()
    file_stream.write(plain_text.encode('utf-8'))
    file_stream.seek(0)
    return file_stream

@app.route('/')
def index():
    previous_chats = get_last_day_chats()
    formatted_history = []
    for item in current_conversation:
        formatted_query = markdown.markdown(item['query'])
        formatted_response = markdown.markdown(item['response'])
        formatted_response = format_code_blocks(formatted_response)
        formatted_response = format_tables(formatted_response)
        formatted_history.append({'query': formatted_query, 'response': formatted_response})
    return render_template('index.html', conversation=formatted_history, previous_chats=previous_chats)

@app.route('/ask', methods=['POST'])
def ask():
    query = request.form['query']
    if not query.strip():
        return jsonify({'error': 'Please enter a question'})

    system_prompt = """When comparing services, provide a Markdown table with:
1. Clear headers in first row
2. Alignment markers in second row (|:---|:---:|)
3. Concise but informative content
4. All major comparison points

When asked to generate documents (leave letters, reports, etc.), provide well-formatted content suitable for conversion to Word, PDF, or TXT files."""

    messages = [
        {"role": "system", "content": system_prompt},
        *[
            {"role": "user" if i % 2 == 0 else "assistant", "content": msg['query'] if i % 2 == 0 else msg['response']}
            for i, msg in enumerate(current_conversation[-3:])
        ],
        {"role": "user", "content": query}
    ]

    try:
        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": messages,
                "temperature": 0.7
            }
        )
        response.raise_for_status()
        reply = response.json()['choices'][0]['message']['content']
        current_conversation.append({'query': query, 'response': reply})

        formatted_reply = markdown.markdown(reply)
        formatted_reply = format_code_blocks(formatted_reply)
        formatted_reply = format_tables(formatted_reply)

        return jsonify({'response': formatted_reply, 'raw_response': reply})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate_document', methods=['POST'])
def generate_document():
    data = request.json
    content = data.get('content', '')
    doc_type = data.get('type', 'docx')
    
    if not content:
        return jsonify({'error': 'No content provided'}), 400
    
    try:
        if doc_type == 'docx':
            file_stream = generate_word_document(content)
            return send_file(
                file_stream,
                as_attachment=True,
                download_name='document.docx',
                mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            )
        elif doc_type == 'pdf':
            file_stream = generate_pdf_document(content)
            return send_file(
                file_stream,
                as_attachment=True,
                download_name='document.pdf',
                mimetype='application/pdf'
            )
        elif doc_type == 'txt':
            file_stream = generate_txt_document(content)
            return send_file(
                file_stream,
                as_attachment=True,
                download_name='document.txt',
                mimetype='text/plain'
            )
        else:
            return jsonify({'error': 'Invalid document type'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ... [keep all other existing routes the same] ...

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
