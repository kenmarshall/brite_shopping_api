import os
from app import create_app

flask_env = os.getenv('FLASK_ENV', 'development')

app, celery = create_app(flask_env)

if __name__ == "__main__":
    app.run(debug=True)
