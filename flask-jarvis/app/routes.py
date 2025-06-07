from flask import Blueprint, request, jsonify, render_template
from app.listener import listen, respond 
from app.audio_getter import get_upload_path, process_audio
import os

main = Blueprint("main", __name__)

@main.route("/")
def home():
    return render_template("index.html")

@main.route("/upload", methods=["POST"])
def upload_audio(): 
    if 'audio' not in request.files: 
        return jsonify({"error": "No audio file uploaded"}), 400
    
    file = request.files['audio']
    wav_path = process_audio(file)
    print(f"WAV file saved to: {wav_path}")
    print(f"File size: {os.path.getsize(wav_path)} bytes")
    transcript = listen(wav_path)
    
    response = respond(transcript)
    return jsonify({"transcript": transcript, "response": response}), 200