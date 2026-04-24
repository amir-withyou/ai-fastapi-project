from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import FileResponse
import cv2
from gtts import gTTS
import pygame
import time

app = FastAPI()

# ================== الصوت ==================
def speak(text):
    pygame.mixer.init()
    tts = gTTS(text, lang='en')
    tts.save("voice.mp3")

    pygame.mixer.music.load("voice.mp3")
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        time.sleep(0.1)

# ================== AI ==================
class TextInput(BaseModel):
    text: str

@app.post("/ai")
def ai_response(data: TextInput):
    text = data.text.lower()

    if "hello" in text:
        response = "Hello! How are you?"
    elif "your name" in text:
        response = "I am your AI assistant."
    elif "bye" in text:
        response = "Goodbye!"
    else:
        response = "Tell me more."

    speak(response)
    return {"response": response}

# ================== Quiz ==================
jobs = {
    "programmer": [
        ("What is Python?", "programming"),
        ("What is a variable?", "data"),
        ("What is a loop?", "repeat"),
    ],
    "doctor": [
        ("What is blood pressure?", "blood"),
        ("What is diabetes?", "sugar"),
        ("What is a virus?", "micro"),
    ]
}

@app.get("/quiz/{job}")
def get_quiz(job: str):
    if job not in jobs:
        return {"error": "Job not found"}

    return {"questions": [q for q, _ in jobs[job]]}


class Answer(BaseModel):
    job: str
    answers: list

@app.post("/quiz/submit")
def submit_quiz(data: Answer):
    if data.job not in jobs:
        return {"error": "Job not found"}

    score = 0
    correct_answers = jobs[data.job]

    for user_ans, (_, correct) in zip(data.answers, correct_answers):
        if correct in user_ans.lower():
            score += 1

    return {
        "score": score,
        "total": len(correct_answers)
    }

# ================== الكاميرا ==================
@app.get("/camera")
def get_camera():
    cap = cv2.VideoCapture(0)

    ret, frame = cap.read()
    cap.release()

    if not ret:
        return {"error": "Camera not working"}

    filename = "frame.jpg"
    cv2.imwrite(filename, frame)

    return FileResponse(filename)

# ================== الصفحة الرئيسية ==================
@app.get("/")
def home():
    return {"message": "Server is working 🚀"}