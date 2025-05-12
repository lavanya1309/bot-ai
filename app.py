from flask import Flask, render_template, request
import wikipedia

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    query = request.form['query']
    try:
        # Fetch a summary from Wikipedia for the query
        summary = wikipedia.summary(query, sentences=3)
        return render_template('index.html', response=summary, query=query)
    except wikipedia.exceptions.DisambiguationError as e:
        # Handle disambiguation error if Wikipedia returns multiple options
        return render_template('index.html', response="Sorry, there are multiple results. Please refine your query.", query=query)
    except wikipedia.exceptions.HTTPTimeoutError:
        return render_template('index.html', response="Request to Wikipedia timed out. Please try again.", query=query)
    except wikipedia.exceptions.RequestError:
        return render_template('index.html', response="There was an error with the Wikipedia request. Please try again later.", query=query)
    except Exception as e:
        return render_template('index.html', response="Sorry, something went wrong. Please try again.", query=query)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
