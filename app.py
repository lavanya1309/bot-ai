from flask import Flask, render_template, request, jsonify
import requests
import re
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# Groq AI API configuration
GROQ_API_KEY = "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"  # Replace with your actual Groq API key
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
                    last_day_chats.append({'filename': filename, 'summary': summary, 'timestamp': chat_time.strftime("%H:%M")})
            else:
                break
        except ValueError:
            continue
    return last_day_chats

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

@app.route('/get_last_day_chats', methods=['GET'])
def get_last_day_chats_ajax():
    chats = get_last_day_chats()
    return jsonify(chats)

@app.route('/')
def index():
    previous_chats = get_last_day_chats()
    formatted_history = []
    for item in current_conversation:
        formatted_query = markdown.markdown(item['query'])
        formatted_response = format_code_blocks(markdown.markdown(item['response']))
        formatted_history.append({'query': formatted_query, 'response': formatted_response})
    return render_template('index.html', conversation=formatted_history, previous_chats=previous_chats)

@app.route('/ask', methods=['POST'])
def ask():
    query = request.form['query']
    if not query.strip():
        return jsonify({'error': 'Please enter a question', 'is_error': True, 'response': ''})

    # --- Medical Question Filtering ---
    medical_keywords = [
        "fever", "cough", "pain", "diagnosis", "treatment", "symptoms", "doctor", "medication", "disease", "illness",
        "prescription", "hospital", "clinic", "medical", "health", "wellness", "anatomy", "physiology", "pathology",
        "infection", "virus", "bacteria", "inflammation", "allergy", "injury", "wound", "fracture", "sprain",
        "burn", "rash", "itching", "swelling", "nausea", "vomiting", "diarrhea", "constipation", "headache",
        "dizziness", "fatigue", "weakness", "chest pain", "shortness of breath", "palpitations", "blood pressure",
        "heart rate", "glucose", "cholesterol", "insulin", "vaccine", "immunization", "therapy", "surgery",
        "rehabilitation", "prognosis", "complication", "acute", "chronic", "benign", "malignant", "tumor", "cancer",
        "arthritis", "asthma", "diabetes", "hypertension", "cardiovascular", "neurological", "gastrointestinal",
        "respiratory", "endocrine", "urological", "gynecological", "pediatric", "geriatric", "ophthalmology",
        "dermatology", "psychiatry", "allergy", "immunology", "pharmacology", "radiology", "anesthesia",
        "nurse", "physician", "surgeon", "pharmacist", "therapist", "specialist", "emergency", "urgent care",
        "first aid", "recovery", "remission", "relapse", "terminal", "palliative", "contagious", "hereditary",
        "genetic", "syndrome", "condition", "disorder", "care", "support", "well-being", "prevention",
        "screening", "check-up", "vaccination", "immunodeficiency", "autoimmune", "transplant", "dialysis",
        "radiotherapy", "chemotherapy", "antibiotics", "antivirals", "antifungals", "analgesics", "antihistamines",
        "steroids", "sedatives", "antidepressants", "antipsychotics", "vaccinate", "immunize", "treat", "cure",
        "manage", "alleviate", "mitigate", "monitor", "assess", "evaluate", "examine", "diagnose", "prescribe",
        "operate", "rehabilitate", "recover", "heal", "suffer", "afflict", "contract", "develop", "experience",
        "report", "complain", "indicate", "suggest", "imply", "manifest", "present", "undergo", "receive",
        "administer", "apply", "ingest", "inject", "inhale", "exhale", "secrete", "excrete", "metabolize",
        "absorb", "distribute", "eliminate", "mutate", "proliferate", "regenerate", "degenerate", "atrophy",
        "hypertrophy", "neoplasia", "metastasis", "ischemia", "infarction", "hemorrhage", "thrombosis", "embolism",
        "edema", "necrosis", "apoptosis", "inflammation", "infection", "infestation", "colonization", "virulence",
        "pathogenicity", "immunity", "antigen", "antibody", "lymphocyte", "phagocyte", "cytokine", "hormone",
        "enzyme", "neurotransmitter", "receptor", "ion channel", "membrane", "nucleus", "cytoplasm", "organelle",
        "tissue", "organ", "system", "apparatus", "tract", "gland", "nerve", "vessel", "muscle", "bone", "joint",
        "skin", "hair", "nail", "eye", "ear", "nose", "throat", "mouth", "tongue", "teeth", "gum", "saliva",
        "esophagus", "stomach", "intestine", "liver", "pancreas", "kidney", "bladder", "ureter", "urethra",
        "lung", "bronchus", "alveoli", "trachea", "larynx", "pharynx", "heart", "artery", "vein", "capillary",
        "brain", "spinal cord", "neuron", "synapse", "skull", "rib", "vertebra", "pelvis", "femur", "tibia",
        "fibula", "humerus", "radius", "ulna", "carpals", "metacarpals", "phalanges", "tarsals", "metatarsals",
        "ligament", "tendon", "cartilage", "blood", "plasma", "red blood cell", "white blood cell", "platelet",
        "lymph", "mucus", "pus", "urine", "feces", "sweat", "tears", "semen", "ovum", "fetus", "embryo",
        "placenta", "umbilical cord", "gene", "chromosome", "DNA", "RNA", "protein", "cell", "molecule", "atom"
    ]
    is_medical_query = any(keyword in query.lower() for keyword in medical_keywords)

    if not is_medical_query:
        non_medical_response = "I can only answer medical-related questions. Please ask me something related to health or medical topics."
        return jsonify({'response': non_medical_response, 'is_error': False})
    # --- End of Filtering ---

    try:
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant specialized in providing information and guidance on medical topics. Only answer questions that are directly related to health, medicine, diseases, symptoms, treatments, and general well-being. If a question is outside of the medical domain, politely decline to answer and state that you can only assist with medical inquiries."},
            *[{"role": "user" if i % 2 == 0 else "assistant", "content": msg['query'] if i % 2 == 0 else msg['response']}
              for i, msg in enumerate(current_conversation[-3:])],
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
        print(f"Groq Response: {result}")

        reply = result['choices'][0]['message']['content']

        current_conversation.append({'query': query, 'response': reply})

        formatted_reply = format_code_blocks(markdown.markdown(reply))
        print(f"Flask Response: {jsonify({'response': formatted_reply, 'is_error': False})}")

        return jsonify({'response': formatted_reply, 'is_error': False})

    except requests.exceptions.RequestException as e:
        error_message = f"API request failed: {str(e)}"
        print(f"Flask Error (RequestException): {error_message}")
        return jsonify({'error': error_message, 'is_error': True, 'response': 'An error occurred while processing your medical question.'})
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(f"Flask Error (General): {error_message}")
        return jsonify({'error': error_message, 'is_error': True, 'response': 'An unexpected error occurred.'})

@app.route('/new_chat', methods=['POST'])
def new_chat():
    global current_conversation
    if current_conversation:
        save_chat_history(current_conversation)
    current_conversation = []
    return jsonify({'success': True})

@app.route('/load_chat', methods=['POST'])
def load_chat():
    filename = request.form['filename']
    try:
        global current_conversation
        current_conversation = load_chat_history(filename)
        formatted_history = []
        for item in current_conversation:
            formatted_query = markdown.markdown(item['query'])
            formatted_response = format_code_blocks(markdown.markdown(item['response']))
            formatted_history.append({'query': formatted_query, 'response': formatted_response})
        return jsonify({'success': True, 'conversation': formatted_history})
    except FileNotFoundError:
        return jsonify({'error': 'Chat history not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Error loading chat: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
