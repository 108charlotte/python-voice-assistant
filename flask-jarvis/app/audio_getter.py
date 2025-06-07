import os
from datetime import datetime
from pydub import AudioSegment

def get_upload_path(): 
    folder = os.path.join("audio_input")
    os.makedirs(folder, exist_ok=True)
    filename = datetime.now().strftime("upload_%Y%m%d_%H%M%S.wav")
    return os.path.join(folder, filename)

def process_audio(file_storage, upload_dir="audio_input"): 
    os.makedirs(upload_dir, exist_ok=True)

    raw_path = os.path.join(upload_dir, "raw.webm")
    wav_path = os.path.join(upload_dir, "input.wav")

    file_storage.save(raw_path)

    audio = AudioSegment.from_file(raw_path)
    # Force channels, sample width, frame rate
    audio = audio.set_channels(1)          # Mono
    audio = audio.set_sample_width(2)      # 16-bit = 2 bytes
    audio = audio.set_frame_rate(16000)    # 16kHz sample rate
    audio.export(wav_path, format="wav")

    return wav_path