import vosk
import json
import requests
import pyttsx3
import wave
from pydub import AudioSegment
import os
import glob
import time
import asyncio
import edge_tts

# load Vosk model
model = vosk.Model("model")
recognizer = vosk.KaldiRecognizer(model, 16000)

# read and transcribe audio file
transcribed_text = ""
audio_file = "harvard_16k.wav"

with wave.open(audio_file, "rb") as wf:
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

# determine appropriate response
def get_response(text):
    text = text.lower()
    if "hello" in text:
        return "Hello! How can I help you today?"

    url = "https://ai.hackclub.com/chat/completions"
    headers = {"Content-Type": "application/json"}
    data = {
        "messages": [{"role": "user", "content": text}]
    }

    response = requests.post(url, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]

# get response to input
ai_response = get_response(transcribed_text)
print("AI Response:", ai_response)

# set up folder to store audio chunk files
chunk_folder = "chunks"
if not os.path.exists(chunk_folder):
    os.makedirs(chunk_folder)

# clear existing chunk files
for f in glob.glob(os.path.join(chunk_folder, "*.wav")): 
    os.remove(f)

# chunk audio so that voice doesn't break
def chunk_text(text, max_length=200): 
    words = text.split()
    chunks = []
    chunk = ""
    for word in words: 
        if len(chunk) + len(word) + 1 <= max_length: 
            chunk += word + " "
        else: 
            chunks.append(chunk.strip())
            chunk = word + " "
    if chunk: 
        chunks.append(chunk.strip())
    return chunks

chunks = chunk_text(ai_response)
chunk_folder = "chunks"
os.makedirs(chunk_folder, exist_ok=True)

async def synthesize_chunk(i, chunk):
    output_path = os.path.join(chunk_folder, f"chunk_{i}.mp3")
    print(f"[INFO] Synthesizing chunk {i} with edge-tts: {chunk}")
    communicate = edge_tts.Communicate(chunk, "en-GB-RyanNeural")
    await communicate.save(output_path)

async def synthesize_all_chunks():
    for i, chunk in enumerate(chunks):
        await synthesize_chunk(i, chunk)

asyncio.run(synthesize_all_chunks())

combined = AudioSegment.empty()
for i in range(len(chunks)):
    mp3_file = os.path.join(chunk_folder, f"chunk_{i}.mp3")
    seg = AudioSegment.from_file(mp3_file, format="mp3")
    combined += seg

combined.export("output.wav", format="wav")