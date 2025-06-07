from flask import Flask
import os

def create_app(): 
    base_dir = os.path.abspath(os.path.dirname(__file__))
    templates_dir = os.path.join(base_dir, '..', 'templates')
    app = Flask(__name__, template_folder=templates_dir, static_url_path="/static", static_folder="static")
    print("Template folder path:", app.jinja_loader.searchpath)
    from .routes import main
    app.register_blueprint(main)
    return app