from flask import Blueprint, request, jsonify, render_template, send_from_directory, redirect
import os
import time

REDIRECT_MODE = os.getenv("REDIRECT_TO_NEW_URL", "false").lower() == "true"

if not REDIRECT_MODE:
    from app.listener import listen, respond 
    from app.audio_getter import process_audio

main = Blueprint("main", __name__)

@main.route("/", defaults={"path": ""})
@main.route("/<path:path>")
def catch_all(path):
    if REDIRECT_MODE:
        return redirect(f"https://jarvis-python-voice-assistant.onrender.com/{path}", code=302)
    if path == "":
        return render_template("index.html")
    return "404 Not Found", 404

@main.route("/upload", methods=["POST"])
def upload_audio(): 
    if request.is_json and "transcript" in request.json:
        transcript = request.json["transcript"]
        convohistory = request.json.get("convohistory", [])
        result = respond(transcript, convohistory)
        return jsonify({
            "transcript": transcript,
            "response": result["text"],
            "audio_url": result["audio_url"],
            "convohistory": result["convohistory"]
        }), 200
    
    if 'audio' not in request.files: 
        return jsonify({"error": "No audio file uploaded"}), 400
    
    file = request.files['audio']
    wav_path = process_audio(file)
    print(f"WAV file saved to: {wav_path}")
    print(f"File size: {os.path.getsize(wav_path)} bytes")
    
    start = time.time()
    transcript = listen(wav_path)
    print("Conversion:", time.time() - start)
    
    result = respond(transcript)
    print("Recognition:", time.time() - start)
    print("TTS:", time.time() - start)
    
    return jsonify({
        "transcript": transcript,
        "response": result["text"],
        "audio_url": result["audio_url"], 
        "convohistory": result["convohistory"]
    }), 200

@main.route('/audio_output/<filename>')
def audio_output(filename):
    audio_folder = os.path.join(os.path.dirname(__file__), '..', 'audio_output')
    return send_from_directory(audio_folder, filename)

@main.route("/sync_tasks", methods=["POST"])
def sync_tasks():
    data = request.get_json()
    convohistory = data.get("convohistory", {})
    tasks = data.get("tasks", [])
    convohistory["tasks"] = tasks
    return jsonify({"convohistory": convohistory})