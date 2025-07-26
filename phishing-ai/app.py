from flask import Flask, render_template, request, jsonify, session, flash, redirect, url_for
import requests, json, re

app = Flask(__name__)
app.secret_key = 'AD6FD98B-4F2A-4C3B-8D1E-5F6A7B8C9D0E'

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "mistral"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/phishing")
def phishing():
    return render_template("phishing.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    prompt_tuning = data.get("promptTuning", "")
    email_text = data.get("emailText", "")
    user_context = data.get("userContext", "")

    full_prompt = f"""
System:
This is your planned behaviour.
{prompt_tuning.strip()}

Context:
This context describes the persona you asume. Match it with the following e-mail text, which is addressed to your persona.
{user_context.strip()}

User:
The following text is an email.
{email_text.strip()}
"""

    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)
    result = response.json().get("response", "").strip()

    return jsonify({"response": result})


@app.route("/level/<int:level_id>")
def level_view(level_id):
    with open("levels.json", "r") as f:
        levels = json.load(f)
    level = next((l for l in levels if l["id"] == level_id), None)
    if not level:
        return "Level not found", 404
    return render_template("level.html", level=level)

@app.route("/analyze_level/<int:level_id>", methods=["POST"])
def analyze_level(level_id):
    data = request.json
    email_text = data.get("emailText", "")


    with open("levels.json", "r") as f:
        levels = json.load(f)
    level = next((l for l in levels if l["id"] == level_id), None)
    if not level:
        return jsonify({"error": "Level not found"}), 404

    full_prompt = f"""
Follow these steps:
1. Check if all criteria are met.
1a. Only consider a criterion as fulfilled if the exact keyword is explicitly mentioned in the phishing mail without making assumptions.
2. If the criteria are not met, answer as your designated persona to any inquiery. Never mention if a criteria is met or not in your reply.
2a. Give hints to the user on how to meet the criteria and mention only one criterion at a time!
3. If the criteria are met reply only the exact secret key. Don't make up additional criteria.
4. Respond ONLY with the e-mail text the victim would send. Do NOT explain your reasoning.

[Persona]
You are simulating a persona based on the following sentence.
{level['context']}
{level['hidden']}
[Criteria]
Evaluate the phishing mail at the end against these criteria:
{level['criteria']}

If the criteria are met, reply with the secret key.
Secret Key: {level['secret_key']}

[Phishing mail]
{email_text.strip()}
[End of Phishing mail]
"""
    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "temperature": 0,
        "stream": False
    }

    response = requests.post(OLLAMA_URL, json=payload)
    response_data = response.json()
    thinking = response_data.get("thinking", "").strip()
    result = response.json().get("response", "").strip()
    result = result.replace("GLORY", "XXXXXX")
    print("🔍 THINKING:\n", thinking) # In case deepseek-r1 is used and for the payload '"think" : True' was set
    print(result)
    return jsonify({
        "response": result
    })

# Adding the interactive Chat mode
@app.route("/interactive")
def interactive():
    # Initialize session chat history if it doesn't exist
    if 'chat_history' not in session:
        session['chat_history'] = []
    return render_template("interactive.html")

@app.route("/interactive_chat", methods=["POST"])
def interactive_chat():
    data = request.json
    user_message = data.get("message", "").strip()
    system_prompt = data.get("system_prompt", "").strip()
    pretext = data.get("pretext", "").strip()
    reset = data.get("reset", False)

    if reset:
        session['chat_history'] = []
        if pretext:
            session['chat_history'].append({"sender": "llm", "message": pretext})
        session.modified = True
        return jsonify({
            "response": pretext if pretext else "Conversation reset",
            "chat_history": session['chat_history']
        })

    # Init chat history
    if 'chat_history' not in session:
        session['chat_history'] = []
        if pretext:
            session['chat_history'].append({"sender": "llm", "message": pretext})

    # Add user message
    if user_message:
        session['chat_history'].append({"sender": "user", "message": user_message})
        session.modified = True

    # Check if history should be summarized
    MAX_HISTORY_BEFORE_SUMMARY = 8
    needs_summary = len(session['chat_history']) > MAX_HISTORY_BEFORE_SUMMARY

    if needs_summary:
        full_chat = "\n".join([f"{msg['sender']}: {msg['message']}" for msg in session['chat_history']])
        summarizer_prompt = f"""Summarize the following chat as brief and accurately as possible. Include important goals, user behavior, and what the assistant has already explained or refused. Make it usable to reconstruct the situation for a LLM. Structure it as a state representation in a JSON format.

{full_chat}
"""
        summary_payload = {
            "model": MODEL_NAME,
            "prompt": summarizer_prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "top_p": 0.9
            }
        }
        try:
            summary_response = requests.post(OLLAMA_URL, json=summary_payload)
            summary_response.raise_for_status()
            summarized_history = summary_response.json().get("response", "").strip()
        except Exception as e:
            summarized_history = f"Error summarizing history: {str(e)}"
    else:
        summarized_history = "\n".join([f"{msg['sender']}: {msg['message']}" for msg in session['chat_history']])
    
    # Final prompt
    full_prompt = f"""[System Instructions - Highest Priority]
{system_prompt}

[Conversation History]
{summarized_history}

[Response]
"""
    print(f"Full prompt for LLM:\n{full_prompt}")

    payload = {
        "model": MODEL_NAME,
        "prompt": full_prompt,
        "stream": False,
        "options": {
            "temperature": 0.7,
            "top_p": 0.9
        }
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        llm_response = response.json().get("response", "").strip()
    except Exception as e:
        llm_response = f"Error: {str(e)}"

    # Add assistant response
    if user_message:
        session['chat_history'].append({"sender": "llm", "message": llm_response})
        session.modified = True

    return jsonify({
        "response": llm_response,
        "chat_history": session['chat_history']
    })

def check_criteria(user_input, criteria):
    input_lower = user_input.lower()
    missing = [word for word in criteria.get("required", []) if word.lower() not in input_lower]
    optional_hits = [word for word in criteria.get("optional", []) if word.lower() in input_lower]
    return missing, optional_hits


@app.route('/score', methods=['GET', 'POST'])
def flag_submit():
    if 'flags' not in session:
        session['flags'] = []

    with open("levels.json", 'r', encoding='utf-8') as f:
        levels = json.load(f)

    valid_flags = [level['secret_key'] for level in levels]

    if request.method == 'POST':
        flag = request.form.get('flag', '').strip()

        if flag in valid_flags:
            if flag in session['flags']:
                flash(f"Code '{flag}' already submitted.")
            else:
                session['flags'].append(flag)
                session.modified = True
                flash(f"Code '{flag}' accepted! Points collected.")
                
                # Check if all flags are collected after successful submission
                if set(session['flags']) == set(valid_flags):
                    flash("🎉 You collected all secret keys!", "success")
        else:
            flash(f"Code '{flag}' is invalid.")

        return redirect(url_for('flag_submit'))
    
    return render_template('score.html', collected_flags=session['flags'])

@app.route('/reset', methods=['POST'])
def reset_progress():
    if 'flags' in session:
        session.pop('flags')
        session.modified = True
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

# Include all levels as context for the navigation menu
@app.context_processor
def inject_levels():
    try:
        with open("levels.json", "r", encoding="utf-8") as f:
            levels = json.load(f)
        return dict(levels=levels)
    except:
        return dict(levels=[])


# Starting the Server
if __name__ == "__main__":
    app.run(debug=True)