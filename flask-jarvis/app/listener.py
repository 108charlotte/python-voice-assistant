import vosk
import json
import requests
import wave
from pydub import AudioSegment
import os
import glob
import asyncio
import edge_tts
import re

# load vosk model
model_path = os.path.join(os.path.dirname(__file__), '..', 'model')
vosk_model = vosk.Model(model_path)

def listen(audio_path): 
    recognizer = vosk.KaldiRecognizer(vosk_model, 16000)

    # read and transcribe audio file
    transcribed_text = ""

    with wave.open(audio_path, "rb") as wf:
        if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
            raise ValueError("Audio file must be WAV format mono PCM 16-bit 16kHz.")
        
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                transcribed_text += result.get("text", "") + " "

        final_result = json.loads(recognizer.FinalResult())
        transcribed_text += final_result.get("text", "")

    print("Transcribed Text:", transcribed_text.strip())
    return transcribed_text.strip()

def respond(text): 
    def get_response(text):
        text = text.lower()
        if "can you hear me" in text:
            return "Unfortunately"
        

        url = "https://ai.hackclub.com/chat/completions"
        headers = {"Content-Type": "application/json"}
        data = {
            "messages": [{"role": "user", "content": text}]
        }

        response = requests.post(url, headers=headers, json=data)
        return response.json()["choices"][0]["message"]["content"]

    ai_response = get_response(text)
    print("AI Response:", ai_response)
    
    output_folder = os.path.join(os.path.dirname(__file__), '..', 'audio_output')
    os.makedirs(output_folder, exist_ok=True)

    ai_response = remove_markdown(ai_response)

    # Synthesize the whole response as one file
    output_path = os.path.join(output_folder, "output.mp3")
    print(f"[INFO] Synthesizing with edge-tts: {ai_response}")
    communicate = edge_tts.Communicate(ai_response, "en-GB-RyanNeural")
    asyncio.run(communicate.save(output_path))

    # Convert to wav
    audio = AudioSegment.from_file(output_path, format="mp3")
    public_audio_path = os.path.join(output_folder, 'output.wav')
    audio.export(public_audio_path, format="wav")

    return {
        "text": ai_response, 
        "audio_url": "/audio_output/output.wav"
    }

def remove_markdown(text): 
    clean = re.sub(r'(\*{1,2}|_{1,2}|~{2}|`{1,3})', '', text)
    return clean