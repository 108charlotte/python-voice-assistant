import vosk
import json
import requests
import wave
from pydub import AudioSegment
import os
import asyncio
import edge_tts
import re
import uuid
import time

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

def respond(text, convohistory=None): 
    if convohistory is None:
        convohistory = []

    convohistory.append({"role": "user", "content": text.strip()})

    def get_response(text, convohistory):
        text = text.lower()
        url = "https://ai.hackclub.com/chat/completions"
        headers = {"Content-Type": "application/json"}
        base = (
            "You are Jarvis, a witty and slightly snarky AI assistant. "
            "Your user is an intelligent teenager who you sometimes tease, but you are never mean or hurtful. "
            "Your responses are being spoken aloud. "
            "Be concise and clear, but answer helpfully and completely. "
            "Do not include stage directions, tone descriptions, or bracketed instructions. "
            "Do not mention sensitive topics like politics, religion, or violence. "
            "You are not a therapist, and you do not give advice. "
            "You are helpful, but you are not overly polite. "
        )

        if "focus" in text and ("begin" in text or "activate" in text or "start" in text): 
            # custom system prompt for focus mode
            url = "https://ai.hackclub.com/chat/completions"
            headers = {"Content-Type": "application/json"}
            data = {
                "messages": [
                    {"role": "system", "content": base + "The user just activated focus mode, and you have just said 'Activating Focus mode. Please stand by...'. Conclude with a witty, sarcastic, or motivational one-liner about focusing or being productive."},
                    {"role": "user", "content": text}
                ]
            }
            response = requests.post(url, headers=headers, json=data)
            return response.json()["choices"][0]["message"]["content"]

        data = {
            "messages": [{"role": "system", "content": base}] + convohistory
        }

        response = requests.post(url, headers=headers, json=data)
        return response.json()["choices"][0]["message"]["content"]

    ai_response = get_response(text, convohistory)
    print(f"AI Response: '{ai_response}'")

    if not ai_response or not ai_response.strip():
        return {
            "text": "Sorry, I couldn't generate a response.",
            "audio_url": None, 
            "convohistory": convohistory
        }
    
    convohistory.append({"role": "assistant", "content": ai_response})

    output_folder = os.path.join(os.path.dirname(__file__), '..', 'audio_output')
    os.makedirs(output_folder, exist_ok=True)

    filename = f"{uuid.uuid4()}.mp3"
    output_path = os.path.join(output_folder, filename)

    ai_response = remove_markdown(ai_response).strip()
    ai_response = ai_response.replace("’", "'").replace("“", '"').replace("”", '"')
    ai_response = re.sub(r'\bkiddo\b', '', ai_response, flags=re.IGNORECASE)
    ai_response = re.sub(r'\bkid\b', '', ai_response, flags=re.IGNORECASE)

    print(f"[INFO] Synthesizing with edge-tts: {ai_response}")
    try:
        communicate = edge_tts.Communicate(
            ai_response,
            "en-GB-RyanNeural",
            rate="+20%"
        )
        asyncio.run(communicate.save(output_path))
    except Exception as e:
        print("edge-tts error:", e)
        return {
            "text": ai_response,
            "audio_url": None, 
            "convohistory": convohistory
        }

    # clean up old audio output files (older than 10 minutes)
    now = time.time()
    for fname in os.listdir(output_folder):
        fpath = os.path.join(output_folder, fname)
        if os.path.isfile(fpath) and fname != filename:
            if now - os.path.getmtime(fpath) > 600:  # 600 seconds = 10 minutes
                try:
                    os.remove(fpath)
                except Exception as e:
                    print(f"Could not delete {fpath}: {e}")

    ai_response = ai_response.strip()
    if ai_response.startswith('"') and ai_response.endswith('"'):
        ai_response = ai_response[1:-1].strip()

    return {
        "text": ai_response, 
        "audio_url": f"/audio_output/{filename}",
        "convohistory": convohistory
    }

def remove_markdown(text): 
    clean = re.sub(r'(\*{1,2}|_{1,2}|~{2}|`{1,3})', '', text)
    return clean

'''
import edge_tts, asyncio

async def list_voices():
    voices = await edge_tts.list_voices()
    for v in voices:
        print(v["ShortName"])

asyncio.run(list_voices())
'''