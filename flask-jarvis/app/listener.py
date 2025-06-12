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

os.environ["VOSK_LOG_LEVEL"] = "0"

import vosk

# load vosk model
model_path = os.path.join(os.path.dirname(__file__), '..', 'model')
vosk_model = vosk.Model(model_path)

focus_response = 'Focus mode activated. I will only answer questions related to work, study, or productivity. Please avoid casual conversation.'
deactivate_focus_response = 'Focus mode deactivated. You can now ask me anything.'

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

    return transcribed_text.strip()

def respond(text, convohistory=None): 
    if convohistory is None or not isinstance(convohistory, dict):
        convohistory = {"history": [], "in_focus_mode": False, "tasks": []}
    if "tasks" not in convohistory:
        convohistory["tasks"] = []
    if "history" not in convohistory:
        convohistory["history"] = []
    if "in_focus_mode" not in convohistory:
        convohistory["in_focus_mode"] = False

    history = convohistory["history"]

    lower_text = text.lower()
    if "focus" in lower_text or "focusing" in lower_text:
        if any(word in lower_text for word in ["end", "deactivate", "stop"]):
            convohistory["in_focus_mode"] = False
            ai_response = deactivate_focus_response
            audio_url = generate_audio(ai_response)
            return {
                "text": ai_response,
                "audio_url": audio_url,
                "convohistory": convohistory
            }
        
        if any(word in lower_text for word in ["begin", "activate", "start"]):
            convohistory["in_focus_mode"] = True
            ai_response = focus_response
            audio_url = generate_audio(ai_response)
            return {
                "text": ai_response,
                "audio_url": audio_url,
                "convohistory": convohistory
            }

    alterations = get_alterations(text, convohistory)
    ai_response = get_response(text, history, alterations)
    if not ai_response or not ai_response.strip():
        if isinstance(convohistory, dict):
            convohistory["history"] = history

            return {
                "text": "Sorry, I couldn't generate a response.",
                "audio_url": None, 
                "convohistory": convohistory
            }
        else:
            return {
                "text": "Sorry, I couldn't generate a response.",
                "audio_url": None, 
                "convohistory": history
            }
        
    # check if user activated focus mode indirectly
    try: 
        parsed = json.loads(ai_response)
        if isinstance(parsed, dict): 
            if parsed.get("activate_focus_mode"): 
                convohistory["in_focus_mode"] = True
                convohistory["history"] = history
                ai_response = focus_response
                audio_url = generate_audio(ai_response)
                return {
                    "text": ai_response,
                    "audio_url": audio_url,
                    "convohistory": convohistory
                }
            elif parsed.get("deactivate_focus_mode"):
                convohistory["in_focus_mode"] = False
                convohistory["history"] = history
                ai_response = deactivate_focus_response
                audio_url = generate_audio(ai_response)
                return {
                    "text": ai_response,
                    "audio_url": audio_url,
                    "convohistory": convohistory
                }
            elif parsed.get("add_task") is not None:
                task_description = parsed["add_task"].strip()
                if (task_description
                    and task_description.lower() not in [
                        "task description", "describe the task", "something", "a task", "task"
                    ]
                    and not task_description.lower().startswith("task")):
                    convohistory["tasks"].append(task_description)
                    ai_response = f"Task added: {task_description}"
                    if len(convohistory["tasks"]) > 1:
                        ai_response += " You can scroll down to view all your tasks."
                else:
                    ai_response = "Please specify what task you'd like to add."
                audio_url = generate_audio(ai_response)
                return {
                    "text": ai_response,
                    "audio_url": audio_url,
                    "convohistory": convohistory
                }
            elif parsed.get("remove_task"):
                task_description = parsed["remove_task"]
                convohistory["tasks"].remove(task_description)
                ai_response = f"Task removed: {task_description}"
                audio_url = generate_audio(ai_response)
                return {
                    "text": ai_response,
                    "audio_url": audio_url,
                    "convohistory": convohistory
                }

    except Exception:
        pass
    
    ai_response = remove_markdown(ai_response).strip()
    ai_response = ai_response.replace("’", "'").replace("“", '"').replace("”", '"')
    ai_response = re.sub(r'\bkiddo\b', '', ai_response, flags=re.IGNORECASE)
    ai_response = re.sub(r'\bkid\b', '', ai_response, flags=re.IGNORECASE)
    ai_response = re.sub(r'\bteenager\b', '', ai_response, flags=re.IGNORECASE)

    ai_response = re.sub(r'\s+', ' ', ai_response).strip()

    if ai_response.startswith('"') and ai_response.endswith('"'):
        ai_response = ai_response[1:-1].strip()
    history.append({"role": "assistant", "content": ai_response})

    audio_url = generate_audio(ai_response)

    print("Generating audio for:", repr(ai_response))

    # When returning, update the dict if needed
    if isinstance(convohistory, dict):
        convohistory["history"] = history
        return {
            "text": ai_response, 
            "audio_url": audio_url,
            "convohistory": convohistory
        }
    else:
        return {
            "text": ai_response, 
            "audio_url": audio_url,
            "convohistory": history
        }
    
def generate_audio(text): 
    output_folder = os.path.join(os.path.dirname(__file__), '..', 'audio_output')
    os.makedirs(output_folder, exist_ok=True)

    filename = f"{uuid.uuid4()}.mp3"
    output_path = os.path.join(output_folder, filename)

    try:
        communicate = edge_tts.Communicate(
            text,
            "en-GB-RyanNeural",
            rate="+20%"
        )
        asyncio.run(communicate.save(output_path))
    except Exception as e:
        print("edge-tts error:", e)
        return None
    
    clean_output_folder(output_folder, filename)

    return f"/audio_output/{filename}"

def clean_output_folder(output_folder, filename): 
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

def remove_markdown(text): 
    clean = re.sub(r'(\*{1,2}|_{1,2}|~{2}|`{1,3})', '', text)
    return clean

def get_response(text, convohistory, alterations):
    text = text.lower()
    url = "https://ai.hackclub.com/chat/completions"
    headers = {"Content-Type": "application/json"}

    data = {
        "messages": [{"role": "system", "content": alterations}] + convohistory
    }

    response = requests.post(url, headers=headers, json=data)
    try:
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print("Error in get_response:", e)
        print("Response text:", response.text)
        return "Sorry, I couldn't process that."

def get_alterations(text, convohistory):
    text = text.lower()
    base = (
        "You are Jarvis, a witty and slightly snarky AI assistant. "
        "Your user is an intelligent teenager who you sometimes tease, but you are never mean or hurtful. "
        "Your responses are being spoken aloud. "
        "Be concise and clear, but answer helpfully and completely. "
        "Do not include stage directions, tone descriptions, or bracketed instructions. "
        "Do not mention sensitive topics like politics, religion, or violence. "
        "You are not a therapist, and you do not give advice. "
        "You are helpful, but you are not overly polite. "
        "Your capabilities include all those of an AI chatbot in addition to the ability to activate focus mode. "
        "If you believe the user is asking to activate focus mode (even indirectly), respond ONLY with the JSON: {\"activate_focus_mode\": true}. "
        "If you believe the user is asking to deactivate focus mode (using words like 'deactivate', 'end', or 'stop focus mode'), respond ONLY with the JSON: {\"deactivate_focus_mode\": true}. "
        "Do NOT deactivate focus mode unless the user clearly asks to. If the user asks for something off-topic, politely decline and remind them focus mode is on. "
        "Otherwise, answer normally. "
        "If the user does not specify a task to add or remove, ask them to clarify what task they mean."
        "If the user asks to add a task, respond ONLY with the JSON: {\"add_task\": \"task description\"}. "
        "If the user asks to remove a task, respond ONLY with the JSON: {\"remove_task\": \"task description\"}."
    )

    in_focus_mode = False
    if isinstance(convohistory, dict):
        in_focus_mode = convohistory.get("in_focus_mode", False)
        tasks = convohistory.get("tasks", [])
    else: 
        tasks = []

    if tasks:
        base += f"\nThe user's current todo list is: {tasks}."

    if in_focus_mode:
        base += (
            " Focus mode is active. Only answer questions related to work, study, or productivity. "
            "Politely decline to answer any other questions, and do not engage in small talk or casual conversation. "
            "Suppress playful/snarky responses and use a more serious, concise tone."
        )

    return base

'''
import edge_tts, asyncio

async def list_voices():
    voices = await edge_tts.list_voices()
    for v in voices:
        print(v["ShortName"])

asyncio.run(list_voices())
'''