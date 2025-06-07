import vosk
import json
import requests
import pyttsx3
import wave
from pydub import AudioSegment
import os
import glob
import time

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

# text-to-speech output with pyttsx3
engine = pyttsx3.init()
engine.setProperty('rate', 150)
engine.setProperty('volume', 1.0)

available_voices = engine.getProperty('voices')
print("Available voices:", [voice.id for voice in available_voices])
engine.setProperty('voice', available_voices[1].id)

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
try: 
    for i, chunk in enumerate(chunks):
        filename = os.path.join(chunk_folder, f"chunk_{i}.wav")
        print(f"[INFO] Saving chunk {i}: {chunk}")
        engine.save_to_file(chunk, filename)
        engine.runAndWait()

        if not os.path.isfile(filename):
            raise FileNotFoundError(f"[ERROR] Failed to create {filename}")
        if os.path.getsize(filename) == 0:
            raise ValueError(f"[ERROR] {filename} exists but is empty (0 bytes)")
except KeyboardInterrupt: 
    print("\n[INTERRUPTED] You manually stopped the script with Ctrl+C.")
    exit(1)

engine.runAndWait()

try:
    for i in range(len(chunks)):
        filename = os.path.join(chunk_folder, f"chunk_{i}.wav")
        waited = 0
        print(f"[INFO] Waiting for {filename} to be created...")
        while not os.path.exists(filename):
            time.sleep(0.1)
            waited += 0.1
            if waited % 1 < 0.1:
                print(f"  ...still waiting ({waited:.1f}s)")
            if waited >= 5: 
                raise FileNotFoundError(f"[ERROR] Timed out waiting for {filename}")
except KeyboardInterrupt:
    print("\n[INTERRUPTED] You manually stopped the script with Ctrl+C.")
    exit(1)


print("All chunks saved. Combining...")

# Combine into one audio segment
combined_audio = AudioSegment.empty()
for i in range(len(chunks)):
    filename = os.path.join(chunk_folder, f"chunk_{i}.wav")
    audio_segment = AudioSegment.from_file(filename, format="wav")
    audio_segment = audio_segment.set_frame_rate(16000).set_channels(1).set_sample_width(2)
    combined_audio += audio_segment

output_file = combined_audio.export("output.wav", format="wav")
print("Done. Final output written to output.wav")