from flask import Flask
import os
from .routes import main

def create_app(): 
    base_dir = os.path.abspath(os.path.dirname(__file__))
    project_root = os.path.join(base_dir, '..')  # go up to project root
    templates_dir = os.path.join(project_root, 'templates')
    static_dir = os.path.join(project_root, 'static')  # now points to root/static

    app = Flask(__name__, template_folder=templates_dir, static_folder=static_dir)
    
    app.register_blueprint(main)
    return app