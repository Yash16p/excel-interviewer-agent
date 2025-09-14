
import os
import json
import random
import tempfile
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from dotenv import load_dotenv
from gtts import gTTS
import matplotlib.pyplot as plt

# load environment variables from .env (OPENAI_API_KEY)
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
    raise EnvironmentError("Set OPENAI_API_KEY in your environment or .env file")

client = OpenAI(api_key=OPENAI_API_KEY)
LLM_MODEL = "gpt-4o-mini"  # change if you prefer another model

# -------------------------
# Text-to-Speech (gTTS)
# -------------------------
def text_to_speech_bytes(text):
    """
    Return audio bytes (mp3) produced by gTTS for the given text.
    We save to a tempfile then read bytes to avoid writing into committed files.
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

# -------------------------
# LangChain memory helper
# -------------------------
def get_langchain_memory():
    if LANGCHAIN_AVAILABLE:
        return ConversationBufferMemory(return_messages=True)
    return None

# -------------------------
# Evaluation prompt (neutral)
# -------------------------
def evaluate_with_llm(question_text: str, candidate_answer: str, ideal_answer: str, memory=None):
    """
    Evaluates answer and returns dict:
    {
      "score": int,
      "breakdown": {...},
      "feedback": str,
      "followup": "<optional followup or ''>",
      "clarity": <1-5>,
      "confidence": <1-5>,
      "problem_solving": <1-5>
    }
    """
    history_text = ""
    if memory:
        try:
            past = memory.load_memory_variables({}).get("history", "")
            if past:
                history_text = f"\nCONVERSATION HISTORY:\n{past}\n"
        except Exception:
            history_text = ""

    prompt = f"""
You are a calm, neutral technical interviewer for Excel skills. Remain neutral and professional.
Do NOT use praise words like "excellent" or "great job". Give clear, constructive and neutral feedback.

Consider the question, the candidate's answer, and the ideal/reference answer.

Return ONLY a JSON object with fields:
- score: integer 1-5 (rounded overall rating)
- breakdown: object with Correctness, Efficiency, Clarity, Completeness (each 1-5)
- feedback: one neutral sentence pointing out missing/unclear parts or summarizing what was covered
- followup: optional follow-up question (string). Include followup only if the answer is incomplete (Completeness <= 3 or score between 2 and 4). Otherwise return empty string.
- clarity: 1-5 rating for clarity of expression
- confidence: 1-5 rating for perceived confidence (based on wording; if unknown, give neutral 3)
- problem_solving: 1-5 rating for problem solving approach

QUESTION:
{question_text}

IDEAL ANSWER:
{ideal_answer}

CANDIDATE ANSWER:
{candidate_answer}

Conversation history (if any):
{history_text}
"""

    try:
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a neutral, professional interviewer."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=400,
        )
        text = resp.choices[0].message.content.strip()
        # robust JSON extraction
        first = text.find("{")
        last = text.rfind("}")
        json_text = text[first:last+1] if (first != -1 and last != -1) else text
        out = json.loads(json_text)
        # ensure keys
        out.setdefault("score", int(round(
            sum([out.get("breakdown", {}).get(k, out.get("score", 3)) for k in ["Correctness","Efficiency","Clarity","Completeness"] if isinstance(out.get("breakdown", {}).get(k, None), (int,float))]) / 4
        )) if out.get("breakdown") else out.get("score", 3))
        out.setdefault("breakdown", out.get("breakdown", {"Correctness":3,"Efficiency":3,"Clarity":3,"Completeness":3}))
        out.setdefault("feedback", out.get("feedback",""))
        out.setdefault("followup", out.get("followup",""))
        out.setdefault("clarity", out.get("clarity", out["breakdown"].get("Clarity",3)))
        out.setdefault("confidence", out.get("confidence",3))
        out.setdefault("problem_solving", out.get("problem_solving", out["breakdown"].get("Correctness",3)))
        return out
    except Exception as e:
        # fallback neutral evaluation
        return {
            "score": 3,
            "breakdown": {"Correctness":3,"Efficiency":3,"Clarity":3,"Completeness":3},
            "feedback": f"Neutral placeholder feedback due to error: {str(e)}",
            "followup": "",
            "clarity": 3,
            "confidence": 3,
            "problem_solving": 3
        }

# -------------------------
# Dynamic question generator (API)
# -------------------------
def select_next_question_api(transcript, asked_skills, avg_score):
    """
    Request LLM to generate a next question.
    Returns a dict: {id, question, level, skill_area, ideal}
    """
    # decide difficulty
    difficulty = "basic"
    if avg_score is not None:
        if avg_score >= 4.5:
            difficulty = "advanced"
        elif avg_score >= 3:
            difficulty = "intermediate"
        else:
            difficulty = "basic"

    # suggest skill areas to avoid
    avoid = asked_skills or []
    prompt = f"""
You are an interviewer generating one Excel interview question.
Return JSON ONLY with fields: id (int), question (string), level (basic/intermediate/advanced), skill_area (one of: Formulas, Pivot Tables, Data Cleaning, Productivity/Protection, Reporting), ideal (short ideal answer).

Constraints:
- Level should be: {difficulty}
- Avoid repeating skill areas: {avoid}
- Make question practical, unambiguous, and concise.
- Ideal should be 1-2 sentence summary.
"""
    try:
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a concise and practical Excel question generator."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=300
        )
        text = resp.choices[0].message.content.strip()
        first = text.find("{")
        last = text.rfind("}")
        json_text = text[first:last+1] if (first!=-1 and last!=-1) else text
        q = json.loads(json_text)
        # normalize
        q.setdefault("id", random.randint(1000,9999))
        q.setdefault("question", q.get("question","Explain difference between absolute and relative refs."))
        q.setdefault("level", difficulty)
        q.setdefault("skill_area", q.get("skill_area","Formulas"))
        q.setdefault("ideal", q.get("ideal","Refer to Excel docs."))
        return q
    except Exception:
        # fallback simple questions pool (5 options)
        fallback_pool = [
            {"id":1,"question":"What are absolute and relative references in Excel? Give an example.","level":"basic","skill_area":"Formulas","ideal":"A1 changes when copied; $A$1 fixed."},
            {"id":2,"question":"Write formula to average column A ignoring blanks.","level":"basic","skill_area":"Formulas","ideal":"=AVERAGEIF(A:A,\"<>\")"},
            {"id":3,"question":"How do you remove duplicate rows and handle blanks in a dataset?","level":"intermediate","skill_area":"Data Cleaning","ideal":"Use Remove Duplicates, Filter blanks, Power Query"},
            {"id":4,"question":"How would you build a Pivot Table to show average sales by region?","level":"advanced","skill_area":"Pivot Tables","ideal":"Insert PivotTable; Region in Rows; Sales in Values -> Average"},
            {"id":5,"question":"How to protect formulas but allow edits in certain cells?","level":"basic","skill_area":"Productivity/Protection","ideal":"Unlock editable cells; Protect sheet; lock formula cells."}
        ]
        # choose a fallback not used
        for f in fallback_pool:
            if f["skill_area"] not in avoid:
                return f
        return random.choice(fallback_pool)

# -------------------------
# PDF report (structured)
# -------------------------
def generate_pdf_report(candidate_name, transcript, overall_score, tab_change_count=0, timings=None, total_duration=None):
    """
    Create a PDF bytes report with structured sections:
    - Header, candidate, timestamp
    - Round/Question-by-question with feedback & followups
    - Skill summary table and recommendations
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
    y -= 14
    p.drawString(margin, y, f"Timestamp: {datetime.now().isoformat()}")
    y -= 18
    p.drawString(margin, y, f"Overall Score: {overall_score:.2f}/5")
    y -= 14
    p.drawString(margin, y, f"Tab Changes During Interview: {tab_change_count}")
    y -= 14
    if total_duration:
        p.drawString(margin, y, f"Total Interview Duration: {total_duration}")
    y -= 20
    p.line(margin, y, width-margin, y)
    y -= 18

    # Question details
    for idx, item in enumerate(transcript, 1):
        if y < 120:
            p.showPage()
            y = height - margin
        p.setFont("Helvetica-Bold", 11)
        p.drawString(margin, y, f"Q{idx} ({item.get('skill_area','')}) - {item.get('question')[:80]}")
        y -= 14
        p.setFont("Helvetica", 10)
        p.drawString(margin+8, y, f"Answer: {item.get('answer','')[:200]}")
        y -= 12
        ev = item.get("evaluation", {})
        p.drawString(margin+8, y, f"Score: {ev.get('score','N/A')}/5")
        y -= 12
        if timings and idx-1 < len(timings):
            p.drawString(margin+8, y, f"Time taken: {int(timings[idx-1])} seconds")
            y -= 12
        p.drawString(margin+8, y, f"Feedback: {ev.get('feedback','')[:200]}")
        y -= 12
        if ev.get("followup"):
            p.drawString(margin+8, y, f"Follow-up asked: {ev.get('followup')}")
            y -= 12
            fu_answer = item.get("followup_answer", "")
            p.drawString(margin+16, y, f"Follow-up answer: {fu_answer[:200]}")
            y -= 12
        y -= 6

    # Skill summary
    # compute skill averages
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

    # Recommendations (simple heuristic)
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
    # personalized tip
    p.drawString(margin+8, y, "Personalized next steps:")
    y -= 12
    p.drawString(margin+12, y, "- Practice pivot table scenarios and Power Query for ETL tasks.")
    y -= 12
    p.drawString(margin+12, y, "- Review INDEX/MATCH and dynamic ranges for robust lookups.")
    y -= 12

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer.getvalue()


# -------------------------
# Utility: matplotlib chart to bytes (skill bars)
# -------------------------
def skill_bar_chart_bytes(skill_map):
    # skill_map: {skill: [scores]}
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


