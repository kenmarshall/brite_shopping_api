 
import os
from app import create_app

flask_env = os.getenv('FLASK_ENV', 'development')
_, celery = create_app(flask_env)