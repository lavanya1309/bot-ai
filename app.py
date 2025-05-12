from flask import Flask, render_template, request, jsonify
import wikipedia

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.get_json().get("message")
    try:
        # Use Wikipedia to fetch relevant information
        result = wikipedia.summary(user_msg, sentences=2)
    except wikipedia.exceptions.DisambiguationError as e:
        result = f"Multiple results found: {e.options[:3]}"
    except wikipedia.exceptions.PageError:
        result = "Sorry, I couldn't find any information on that topic."
    except Exception as e:
        result = f"An error occurred: {str(e)}"

    return jsonify({"reply": result})

if __name__ == "__main__":
    app.run(debug=True)
