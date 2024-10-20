from celery import Celery
from flask import Flask


def init_celery(app: Flask, configs, flask_env):
    # Use the environment-specific Celery config section
    celery_configs = configs[f"celery:{flask_env}"]
    
    celery = Celery(app.import_name)

    celery.conf.update({"broker_url": celery_configs["broker_url"]})
    celery.set_default() 
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery