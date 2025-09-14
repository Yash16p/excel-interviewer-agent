# utils.py
import os
import json
import random
import tempfile
import time
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from dotenv import load_dotenv
from gtts import gTTS
import matplotlib.pyplot as plt
from collections import Counter

load_dotenv()

# LangChain memory optional
try:
    from langchain_community.memory import ConversationBufferMemory
    LANGCHAIN_AVAILABLE = True
except Exception:
    try:
        from langchain.memory import ConversationBufferMemory
        LANGCHAIN_AVAILABLE = True
    except Exception:
        LANGCHAIN_AVAILABLE = False

from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError("Set OPENAI_API_KEY in environment or .env")

client = OpenAI(api_key=OPENAI_API_KEY)
LLM_MODEL = "gpt-4o-mini"

# ---------- TTS ----------
def text_to_speech_bytes(text):
    """
    Convert text to mp3 bytes via gTTS.
    Using temp file to get bytes; removes file after.
    """
    if not text:
        return None
    tts = gTTS(text=text, lang="en")
    fd, path = tempfile.mkstemp(suffix=".mp3")
    os.close(fd)
    try:
        tts.save(path)
        with open(path, "rb") as f:
            data = f.read()
    finally:
        try:
            os.remove(path)
        except Exception:
            pass
    return data

# ---------- LangChain memory ----------
def get_langchain_memory():
    if LANGCHAIN_AVAILABLE:
        return ConversationBufferMemory(return_messages=True)
    return None

# ---------- Evaluation ----------
def evaluate_with_llm(question_text: str, candidate_answer: str, ideal_answer: str, memory=None):
    """
    Evaluate an answer using the LLM and return structured dict.
    Neutral tone and optional followup generation.
    """
    history_text = ""
    if memory:
        try:
            mem = memory.load_memory_variables({}).get("history", "")
            if mem:
                history_text = f"\nCONVERSATION HISTORY:\n{mem}\n"
        except Exception:
            history_text = ""

    prompt = f"""
You are a calm, neutral technical interviewer for Excel skills. Be neutral and constructive; avoid praise words (e.g., "excellent") and avoid harsh criticism.

Given the QUESTION, IDEAL ANSWER and CANDIDATE ANSWER, produce a JSON object only (no other text) with the fields:
- score: integer 1-5 (overall)
- breakdown: {{ "Correctness":1-5, "Efficiency":1-5, "Clarity":1-5, "Completeness":1-5 }}
- feedback: one neutral sentence pointing out what was missing or unclear (or summarizing what was correct)
- followup: an optional follow-up question string; include it ONLY if the answer is incomplete or unclear (Completeness <= 3 or score between 2 and 4). Otherwise return empty string.
- clarity: 1-5 rating for clarity of expression
- confidence: 1-5 perceived confidence (if unknown, use 3)
- problem_solving: 1-5 for problem-solving approach

QUESTION:
{question_text}

IDEAL ANSWER:
{ideal_answer}

CANDIDATE ANSWER:
{candidate_answer}

Conversation history:
{history_text}
"""
    try:
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a neutral interviewer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=400,
        )
        text = resp.choices[0].message.content.strip()
        first = text.find("{")
        last = text.rfind("}")
        json_text = text[first:last+1] if (first != -1 and last != -1) else text
        out = json.loads(json_text)
        # ensure keys exist and reasonable defaults
        out.setdefault("breakdown", {"Correctness":3,"Efficiency":3,"Clarity":3,"Completeness":3})
        if "score" not in out:
            br = out["breakdown"]
            out["score"] = int(round((br.get("Correctness",3)+br.get("Efficiency",3)+br.get("Clarity",3)+br.get("Completeness",3))/4))
        out.setdefault("feedback", "")
        out.setdefault("followup", "")
        out.setdefault("clarity", out["breakdown"].get("Clarity",3))
        out.setdefault("confidence", 3)
        out.setdefault("problem_solving", out["breakdown"].get("Correctness",3))
        return out
    except Exception as e:
        return {
            "score": 3,
            "breakdown": {"Correctness":3,"Efficiency":3,"Clarity":3,"Completeness":3},
            "feedback": f"Neutral placeholder feedback due to error: {str(e)}",
            "followup": "",
            "clarity": 3,
            "confidence": 3,
            "problem_solving": 3
        }

# ---------- Question generator ----------
from questions import FALLBACK_QUESTIONS, SKILL_AREAS
def select_next_question_api(transcript, asked_skills, avg_score):
    """
    Ask the LLM to generate a practical question with a short ideal.
    Falls back to static pool on error.
    """
    difficulty = "basic"
    if avg_score is not None:
        if avg_score >= 4.5:
            difficulty = "advanced"
        elif avg_score >= 3:
            difficulty = "intermediate"
        else:
            difficulty = "basic"

    avoid = asked_skills or []
    prompt = f"""
Generate one Excel interview question. Return JSON ONLY with fields:
id (int), question (string), level (basic/intermediate/advanced), skill_area (choose one of {SKILL_AREAS}), ideal (1-2 sentence ideal).

Constraints:
- Prefer level = {difficulty}
- Avoid skill areas: {avoid}
- Make question practical and concise.
"""
    try:
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[{"role":"system","content":"Excel question generator."},{"role":"user","content":prompt}],
            temperature=0.6,
            max_tokens=300
        )
        text = resp.choices[0].message.content.strip()
        first = text.find("{")
        last = text.rfind("}")
        json_text = text[first:last+1] if (first!=-1 and last!=-1) else text
        q = json.loads(json_text)
        q.setdefault("id", random.randint(1000,9999))
        q.setdefault("question", q.get("question","Explain difference between absolute and relative references."))
        q.setdefault("level", difficulty)
        q.setdefault("skill_area", q.get("skill_area", SKILL_AREAS[0]))
        q.setdefault("ideal", q.get("ideal","Refer to Excel docs."))
        return q
    except Exception:
        # fallback that avoids asked_skills
        for f in FALLBACK_QUESTIONS:
            if f["skill_area"] not in avoid:
                return f
        return random.choice(FALLBACK_QUESTIONS)

# ---------- Simple consistency metric ----------
def tokenize_answer(s):
    # simple tokenization, remove punctuation, lowercase
    if not s:
        return set()
    tokens = [w.strip(".,()[]{}:;\"'").lower() for w in s.split()]
    tokens = [t for t in tokens if len(t) > 2]
    return set(tokens)

def jaccard(a, b):
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    inter = a.intersection(b)
    union = a.union(b)
    return len(inter)/len(union) if union else 0.0

def compute_consistency(transcript):
    """
    Compute a simple consistency score 0-1 across consecutive answers using Jaccard
    Returns average consistency (0-1). Map to 1-5 scale when needed.
    """
    tokens_list = [tokenize_answer(t.get("answer","")) for t in transcript]
    if len(tokens_list) < 2:
        return 1.0
    sims = []
    for i in range(1, len(tokens_list)):
        sims.append(jaccard(tokens_list[i-1], tokens_list[i]))
    avg = sum(sims)/len(sims) if sims else 1.0
    return avg

# ---------- Chart & PDF ----------
def skill_bar_chart_bytes(skill_map):
    skills = []
    avgs = []
    for k, vals in skill_map.items():
        skills.append(k)
        avgs.append(sum(vals)/len(vals) if vals else 0)
    fig, ax = plt.subplots(figsize=(6, 3))
    ax.bar(skills, avgs)
    ax.set_ylim(0, 5)
    ax.set_ylabel("Average Score (0-5)")
    ax.set_title("Skill Area Averages")
    plt.tight_layout()
    buf = BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

def generate_pdf_report(candidate_name, transcript, overall_score, tab_change_count=0, timings=None, consistency=None):
    """
    timings: list of seconds per question (same order as transcript)
    """
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin = 40
    y = height - margin

    p.setFont("Helvetica-Bold", 16)
    p.drawString(margin, y, "AI-Powered Excel Mock Interview - Interview Report")
    y -= 26
    p.setFont("Helvetica", 10)
    p.drawString(margin, y, f"Candidate: {candidate_name or 'Anonymous'}")
    y -= 12
    p.drawString(margin, y, f"Timestamp: {datetime.now().isoformat()}")
    y -= 12
    p.drawString(margin, y, f"Overall Score: {overall_score:.2f}/5")
    y -= 12
    p.drawString(margin, y, f"Tab Changes During Interview: {tab_change_count}")
    y -= 12
    p.drawString(margin, y, f"Consistency (0-1): {consistency:.2f}" if consistency is not None else "")
    y -= 16
    p.line(margin, y, width-margin, y)
    y -= 18

    for idx, item in enumerate(transcript, 1):
        if y < 140:
            p.showPage()
            y = height - margin
        p.setFont("Helvetica-Bold", 11)
        qtitle = item.get("question", "")[:100]
        p.drawString(margin, y, f"Q{idx} ({item.get('skill_area','')})")
        y -= 14
        p.setFont("Helvetica", 10)
        p.drawString(margin+8, y, f"Question: {qtitle}")
        y -= 12
        p.drawString(margin+8, y, f"Answer: {item.get('answer','')[:200]}")
        y -= 12
        ev = item.get("evaluation", {})
        p.drawString(margin+8, y, f"Score: {ev.get('score','N/A')}/5")
        y -= 12
        p.drawString(margin+8, y, f"Feedback: {ev.get('feedback','')[:200]}")
        y -= 12
        time_taken = timings[idx-1] if timings and idx-1 < len(timings) else None
        if time_taken is not None:
            p.drawString(margin+8, y, f"Time taken (seconds): {int(time_taken)}")
            y -= 12
        if ev.get("followup"):
            p.drawString(margin+8, y, f"Follow-up asked: {ev.get('followup')}")
            y -= 12
            fu_answer = item.get("followup_answer", "")
            p.drawString(margin+16, y, f"Follow-up answer: {fu_answer[:200]}")
            y -= 12
        y -= 6

    # Skill summary
    skill_map = {}
    for t in transcript:
        sa = t.get("skill_area","General")
        skill_map.setdefault(sa, []).append(t.get("evaluation",{}).get("score",3))
    if y < 160:
        p.showPage()
        y = height - margin
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y, "Skill Summary")
    y -= 14
    p.setFont("Helvetica", 10)
    for sa, vals in skill_map.items():
        avg = sum(vals)/len(vals)
        p.drawString(margin+8, y, f"{sa}: {avg:.2f}/5")
        y -= 12

    # Recommendations
    if y < 120:
        p.showPage()
        y = height - margin
    p.setFont("Helvetica-Bold", 12)
    p.drawString(margin, y, "Recommendations")
    y -= 14
    p.setFont("Helvetica", 10)
    strengths = [k for k,v in skill_map.items() if sum(v)/len(v) >= 4]
    weaknesses = [k for k,v in skill_map.items() if sum(v)/len(v) <= 2.5]
    if strengths:
        p.drawString(margin+8, y, "Strengths: " + ", ".join(strengths))
        y -= 12
    if weaknesses:
        p.drawString(margin+8, y, "Weaknesses: " + ", ".join(weaknesses))
        y -= 12
    p.drawString(margin+8, y, "Personalized next steps:")
    y -= 12
    p.drawString(margin+12, y, "- Practice pivot tables and Power Query for ETL tasks.")
    y -= 12
    p.drawString(margin+12, y, "- Review INDEX/MATCH and dynamic named ranges.")
    y -= 12

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.getvalue()
