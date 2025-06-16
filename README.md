# JARVIS: python-voice-assistant

What it does: 
Python voice assistant (aspiring JARVIS) is a web-based application built on flask which takes audio input from the browser, transcribes it, uses hack club ai to respond, and then converts that response to speech and speaks it back to you using an audio element in html. In addition, it also has the ability to reduce distractions and reduce productivity by activating focus mode, and can keep track of a todo list. 

Why: 
I made this project because I wanted to learn more about LLMs and chatbots, and understand how to utilize them in my programs. I wanted to be able to create a useful assistant that was fully individualized to the user, and who could respond intelligently without utilizing too many preprogrammed responses. 

HOW I made my project: 
- webpack as a bundler
- flask for backend
- html + javascript for visual frontend, filtering through some data, and interpreting backend responses for display
- python backend through flask, utilized vosk for speech --> text (speech received from javascript frontend using speech recognition)
- used hack club unlimited open AI for backend response from AI
- used edge-tts to convert AI response back to speech and play through audio element on html page

Struggles and lessons: 
- instructing the ai: I particularly struggled with getting the AI to only add/remove tasks or activate/deactivate focus mode when the user explicitly requested it
    - learned: importance of specificity in prompting and instruction, along with double-checking responses that the LLM returns
- javascript frontend to flask backend: I struggled a lot with getting the javascript frontend to correctly record user input and send it to the backend
    - learned: how to use speech recognition, how to record audio from browser
- flask backend to javascript frontend: Probably the most frustrating struggle was sending uncorrupted audio data from the AI back to the user. First, I struggled with getting the text to speech to work, and after attempting chunking I ended up switching to edge-tts. After that, I struggled with the audio element not playing on the html page as a result of my javascript code. 
    - learned: sometimes the hardest thing isn't writing the code--its getting the different parts to interact well together