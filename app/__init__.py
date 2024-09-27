from flask import Flask
from flask_restful import Api
from .resources import HelloWorld


def create_app():
    app = Flask(__name__)
    api = Api(app)

    api.add_resource(HelloWorld, "/")

    return app
