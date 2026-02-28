import os
from datetime import datetime
from app import create_app
from dotenv import load_dotenv
from flask import jsonify, render_template

load_dotenv()

flask_env = os.getenv('FLASK_ENV', 'development')

app = create_app(flask_env)

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

@app.route('/')
def landing():
    return render_template('landing.html', year=datetime.now().year)

@app.route('/privacy')
def privacy():
    return render_template('privacy.html', year=datetime.now().year)
