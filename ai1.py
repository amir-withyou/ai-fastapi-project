from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import FileResponse
import cv2
from gtts import gTTS
import os
import uuid
from pathlib import Path
import logging

app = FastAPI()

# إعدادات التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# إنشاء مجلدات للملفات المؤقتة
TEMP_DIR = Path("temp_files")
TEMP_DIR.mkdir(exist_ok=True)

# ================== الصوت ==================
def speak(text):
    """
    تحويل النص إلى صوت باستخدام gTTS
    بدون الاعتماد على pygame (يعمل في بيئة headless)
    """
    try:
        # إنشاء اسم ملف فريد لتجنب التضارب
        voice_file = TEMP_DIR / f"voice_{uuid.uuid4()}.mp3"
        
        # حفظ الملف الصوتي
        tts = gTTS(text, lang='en')
        tts.save(str(voice_file))
        
        logger.info(f"✅ تم إنشاء ملف صوتي: {voice_file}")
        return str(voice_file)
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء الصوت: {e}")
        return None

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

    # محاولة تشغيل الصوت (اختياري في بيئة السيرفر)
    voice_file = speak(response)
    
    return {
        "response": response,
        "voice_file": voice_file
    }

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
    """الحصول على أسئلة الكويز لوظيفة معينة"""
    if job not in jobs:
        return {"error": "Job not found", "available_jobs": list(jobs.keys())}

    return {"job": job, "questions": [q for q, _ in jobs[job]]}


class Answer(BaseModel):
    answers: list

@app.post("/quiz/{job}/submit")
def submit_quiz(job: str, data: Answer):
    """تقديم إجابات الكويز والحصول على النتيجة"""
    if job not in jobs:
        return {"error": "Job not found", "available_jobs": list(jobs.keys())}

    score = 0
    correct_answers = jobs[job]

    # التحقق من عدد الإجابات
    if len(data.answers) != len(correct_answers):
        return {
            "error": f"Expected {len(correct_answers)} answers, got {len(data.answers)}"
        }

    for user_ans, (question, correct) in zip(data.answers, correct_answers):
        if correct in user_ans.lower():
            score += 1

    return {
        "job": job,
        "score": score,
        "total": len(correct_answers),
        "percentage": round((score / len(correct_answers)) * 100, 2)
    }

# ================== الكاميرا ==================
@app.get("/camera")
def get_camera():
    """التقاط صورة من الكاميرا"""
    try:
        cap = cv2.VideoCapture(0)
        
        # التحقق من أن الكاميرا مفتوحة
        if not cap.isOpened():
            return {"error": "Camera not available"}

        ret, frame = cap.read()
        cap.release()

        if not ret:
            return {"error": "Failed to capture frame"}

        # إنشاء اسم ملف فريد
        filename = TEMP_DIR / f"frame_{uuid.uuid4()}.jpg"
        cv2.imwrite(str(filename), frame)
        
        logger.info(f"✅ تم حفظ الصورة: {filename}")
        
        return FileResponse(str(filename), media_type="image/jpeg")
    
    except Exception as e:
        logger.error(f"❌ خطأ في الكاميرا: {e}")
        return {"error": str(e)}

# ================== تنظيف الملفات المؤقتة ==================
@app.get("/cleanup")
def cleanup_temp_files():
    """حذف الملفات المؤقتة القديمة"""
    try:
        deleted_count = 0
        for file in TEMP_DIR.glob("*"):
            if file.is_file():
                file.unlink()
                deleted_count += 1
        
        return {
            "message": "Cleanup completed",
            "deleted_files": deleted_count
        }
    except Exception as e:
        return {"error": str(e)}

# ================== الصفحة الرئيسية ==================
@app.get("/")
def home():
    return {
        "message": "Server is working 🚀",
        "endpoints": {
            "ai": "POST /ai - Send text to AI",
            "quiz": "GET /quiz/{job} - Get quiz questions",
            "quiz_submit": "POST /quiz/{job}/submit - Submit quiz answers",
            "camera": "GET /camera - Take a photo",
            "cleanup": "GET /cleanup - Clean temporary files"
        },
        "available_jobs": list(jobs.keys())
    }
