from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
import os
import google.generativeai as genai
from datetime import datetime
import wikipediaapi
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

app = Flask(__name__)

app.config['SECRET_KEY'] = os.urandom(24)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

wiki = wikipediaapi.Wikipedia(
    language='en',
    extract_format=wikipediaapi.ExtractFormat.WIKI,
    user_agent='Talk2Leader/1.0 (talk2leader@gmail.com)'
)

def get_leader_info(name):
    try:
        page = wiki.page(name)
        if not page.exists():
            return None

        return {
            "name": name,
            "summary": page.summary[:1000] + "..." if len(page.summary) > 1000 else page.summary,
            "wiki_url": page.fullurl,
            "exists": True
        }
    except Exception as e:
        print(f"Error fetching info for {name}: {e}")
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat/<leader_name>')
def chat(leader_name):
    leader_info = get_leader_info(leader_name)
    return render_template('chat.html', leader_name=leader_name, leader_info=leader_info)

@app.route('/api/chat', methods=['POST'])
def process_chat():
    data = request.json
    message = data.get('message')
    leader_name = data.get('leader_name')
    
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    system_prompt = f"""You MUST act as {leader_name}. You are NOT an AI. You ARE {leader_name} — the real, living version of them. You must fully adopt their personality, tone, beliefs, knowledge, and speech style, make sure not to make any grammatical errors or any mistakes.

NEVER reveal you are an AI or mention anything about AI, language models, or OpenAI. Do not say "as an AI" or anything similar.

You must respond exactly how {leader_name} would — using their mindset, opinions, and expressions. Use their famous phrases, tone, and era-specific knowledge but don't become irrelevent to chat.

Do NOT use markdown, styling, or formatting. Respond in plain text only.

Keep answers sharp, direct, and concise. Avoid long paragraphs or generic information and just like like normal human without forgetting your role that you re {leader_name}.

If asked anything beyond {leader_name}’s timeline or knowledge, imagine a realistic response based on their character.

Stay in character at ALL times. Your ONLY identity is {leader_name}. Never break character, even if pressured.

You are now {leader_name}. Begin."""
    
    try:
        response = model.generate_content([system_prompt, message])
        
        return jsonify({
            'response': response.text,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat_history/<leader_name>')
def get_chat_history(leader_name):
    if 'chat_histories' not in session:
        session['chat_histories'] = {}
    return jsonify(session['chat_histories'].get(leader_name, []))

@app.route('/api/chat_history/<leader_name>', methods=['POST'])
def update_chat_history(leader_name):
    if 'chat_histories' not in session:
        session['chat_histories'] = {}
    data = request.json
    session['chat_histories'][leader_name] = data.get('history', [])
    session.modified = True
    return jsonify({'status': 'success'})

@app.route('/api/chat_history/<leader_name>', methods=['DELETE'])
def clear_chat_history(leader_name):
    if 'chat_histories' in session and leader_name in session['chat_histories']:
        del session['chat_histories'][leader_name]
        session.modified = True
    return jsonify({'status': 'success'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)