from flask import Flask, render_template, request
import wikipedia

app = Flask(__name__)

# Set the default Wikipedia language (optional)
wikipedia.set_lang("en")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    query = request.form['query']
    try:
        # Fetch the Wikipedia summary for the query
        response = wikipedia.summary(query, sentences=3)  # Limit the response to 3 sentences
    except wikipedia.exceptions.DisambiguationError as e:
        response = f"Your query is too broad. Did you mean: {', '.join(e.options)}?"
    except wikipedia.exceptions.PageError:
        response = "Sorry, I couldn't find any information on that topic."
    except wikipedia.exceptions.HTTPTimeoutError:
        response = "Timeout error occurred while fetching data from Wikipedia."
    except Exception as e:
        response = f"⚠️ Something went wrong: {str(e)}. Please try again."
    
    return render_template('index.html', query=query, response=response)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
