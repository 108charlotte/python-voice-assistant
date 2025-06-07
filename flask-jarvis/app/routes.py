from flask import Blueprint
from app.listener import listen, respond 

main = Blueprint("main", __name__)

@main.route("/")
def home():
    text = listen()
    respond(text)
    return "Hello from JARVIS!"