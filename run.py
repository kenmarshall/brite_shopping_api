import os
from app import create_app
from dotenv import load_dotenv
from flask import jsonify # Import jsonify

load_dotenv()

flask_env = os.getenv('FLASK_ENV', 'development')

app = create_app(flask_env)

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200
