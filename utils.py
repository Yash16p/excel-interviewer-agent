import os
import json
import random
import tempfile
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from dotenv import load_dotenv
from gtts import gTTS

# Load environment variables
load_dotenv()

# LangChain memory fallback
try:
    from langchain_community.memory import ConversationBufferMemory
    LANGCHAIN_AVAILABLE = True
except ImportError:
    try:
        from langchain.memory import ConversationBufferMemory
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        LANGCHAIN_AVAILABLE = False

from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("Set OPENAI_API_KEY in your .env file.")

client = OpenAI(api_key=OPENAI_API_KEY)

# cost-efficient model
LLM_MODEL = "gpt-4o-mini"


# --- Text to Speech ---
def text_to_speech(text, filename="speech.mp3"):
    """Convert text to speech and return file path for Streamlit."""
    tts = gTTS(text=text, lang="en")
    temp_dir = tempfile.gettempdir()
    filepath = os.path.join(temp_dir, filename)
    tts.save(filepath)
    return filepath


# --- Evaluate Answer ---
def evaluate_with_llm(question_text, candidate_answer, ideal_answer, memory=None):
    """
    Evaluate candidate's answer in a neutral, interviewer-like tone.
    Occasionally suggest a follow-up if the answer is incomplete.
    """

    history_text = ""
    if memory:
        past_msgs = memory.load_memory_variables({}).get("history", "")
        if past_msgs:
            history_text = f"\nCONVERSATION HISTORY:\n{past_msgs}\n"

    prompt = f"""
You are acting as a professional Excel interviewer. 
Your tone must remain neutral and professional at all times. 
Do not use praise words like "excellent" or "great job". 
Do not criticize harshly. 
Provide technical feedback as an interviewer would: 
- Point out what was covered correctly. 
- Mention what was missing or unclear. 
- Suggest improvements if needed.

Additionally, if the candidate's answer seems incomplete (score <=3 or Completeness <=3),
generate ONE optional follow-up question an interviewer might naturally ask 
to clarify their approach. Otherwise, leave follow-up empty.

Return ONLY JSON in the following format:
{{
  "score": <int 1-5>,
  "breakdown": {{
    "Correctness": <int 1-5>,
    "Efficiency": <int 1-5>,
    "Clarity": <int 1-5>,
    "Completeness": <int 1-5>
  }},
  "feedback": "<neutral, professional feedback sentence>",
  "followup": "<optional follow-up question or empty string>"
}}

QUESTION:
{question_text}

IDEAL ANSWER:
{ideal_answer}

CANDIDATE ANSWER:
{candidate_answer}
"""

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a neutral, professional interviewer."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=350,
        )
        text = response.choices[0].message.content.strip()
        first = text.find("{")
        last = text.rfind("}")
        json_text = text[first:last + 1] if (first != -1 and last != -1) else text
        return json.loads(json_text)
    except Exception as e:
        return {
            "score": 3,
            "breakdown": {k: 3 for k in ["Correctness", "Efficiency", "Clarity", "Completeness"]},
            "feedback": f"Neutral placeholder feedback due to error: {str(e)}",
            "followup": ""
        }


# --- Adaptive Question Selection ---
def select_next_question_api(transcript, asked_skills, avg_score):
    """
    Generate the next interview question dynamically using LLM.
    transcript: list of past Q&A with evaluations
    asked_skills: list of skill areas already covered
    avg_score: average score from previous answers
    """
    skills_covered = asked_skills or []

    difficulty = "basic"
    if avg_score and avg_score >= 4:
        difficulty = "advanced"
    elif avg_score and avg_score >= 3:
        difficulty = "intermediate"

    prompt = f"""
    You are an Excel interviewer. Generate ONE clear and specific interview question.
    - Difficulty: {difficulty}
    - Avoid repeating these skill areas: {skills_covered}
    - Make questions specific and unambiguous
    - Focus on practical Excel skills
    - Format as JSON with fields:
      {{
        "id": <random unique int>,
        "question": "<clear, specific question text>",
        "level": "{difficulty}",
        "skill_area": "<skill category>",
        "ideal": "<short ideal answer reference>"
      }}
    """

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful Excel interview question generator."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=400,
        )
        text = response.choices[0].message.content.strip()
        first, last = text.find("{"), text.rfind("}")
        json_text = text[first:last+1] if (first != -1 and last != -1) else text
        return json.loads(json_text)
    except Exception as e:
        return {
            "id": random.randint(1000, 9999),
            "question": "Fallback: Explain the difference between relative and absolute references in Excel.",
            "level": "basic",
            "skill_area": "Formulas",
            "ideal": "Relative references adjust, absolute references ($A$1) stay fixed."
        }


# --- PDF Report Generation ---
def generate_pdf_report(candidate_name, transcript, overall_score):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin = 40
    y = height - margin

    p.setFont("Helvetica-Bold", 16)
    p.drawString(margin, y, "AI-Powered Excel Mock Interview - Feedback Report")
    y -= 30
    p.setFont("Helvetica", 12)
    p.drawString(margin, y, f"Candidate: {candidate_name or 'Anonymous'}")
    y -= 20
    p.drawString(margin, y, f"Overall Score: {overall_score:.2f}/5")
    y -= 30

    for idx, item in enumerate(transcript, start=1):
        if y < 120:
            p.showPage()
            y = height - margin
            p.setFont("Helvetica", 12)
        p.setFont("Helvetica-Bold", 11)
        p.drawString(margin, y, f"Q{idx}: {item['question']}")
        y -= 16
        p.setFont("Helvetica", 10)
        p.drawString(margin + 8, y, f"Answer: {item['answer'][:180]}")
        y -= 14
        ev = item.get("evaluation", {})
        fb = ev.get("feedback", "")
        score = ev.get("score", "")
        p.drawString(margin + 8, y, f"Score: {score}/5 - {fb}")
        y -= 20
        if ev.get("followup"):
            p.drawString(margin + 8, y, f"Follow-up: {ev['followup']}")
            y -= 20

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.getvalue()


# --- LangChain Memory Helper ---
def get_langchain_memory():
    if LANGCHAIN_AVAILABLE:
        return ConversationBufferMemory(return_messages=True)
    else:
        return None


# Legacy evaluator
def evaluate_answer(question, answer):
    ideal_answer = "This is a placeholder ideal answer."
    result = evaluate_with_llm(question, answer, ideal_answer)
    return json.dumps(result)
