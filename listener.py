import vosk
import json

model = vosk.Model("model")

recognizer = vosk.KaldiRecognizer(model, 16000)

audio_file = "harvard_16k.wav"

with open(audio_file, "rb") as audio: 
    while True: 
        data = audio.read(4000)
        if len(data) == 0: 
            break
        if recognizer.AcceptWaveform(data):
            print("✅", json.loads(recognizer.Result()))
        else: 
            print("🟡", json.loads(recognizer.PartialResult()))

print("🏁", json.loads(recognizer.FinalResult()))