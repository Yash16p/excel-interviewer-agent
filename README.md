# 🧑‍💻 Multimodal AI Job Interview Agent

A **fully voice-driven, multimodal AI interview system** that simulates realistic job interviews for multiple roles (Data Scientist, SDE, Data Analyst, etc.). Candidates speak their answers, are monitored via webcam, and are evaluated in real time by an LLM agent that adapts dynamically to their responses. At the end, a recruiter-style PDF report with scores, charts, and recommendations is generated.

This project demonstrates how AI can **fully simulate a professional interview**, combining vision, audio, RAG-based knowledge grounding, and agentic LLM reasoning.

---

## ✨ Key Features

* **Voice-First Interviewing**: Candidates respond using speech; no typing required.
* **Dynamic Adaptive Questions**: LLM generates next questions based on candidate’s previous answers, skill level, and resume.
* **Multimodal Evaluation**: Combines LLM reasoning, speech metrics, and vision metrics (eye contact, posture, facial expressions).
* **Role & Persona Customization**: Candidate selects desired role and interviewer persona (friendly, strict, technical, etc.).
* **RAG-Powered Context**: Ground evaluations and questions with role-specific knowledge documents.
* **Smart Follow-Ups**: Optional clarifying or advanced questions triggered based on previous responses.
* **Tab & Webcam Monitoring**: Detects tab-switching and monitors candidate attention for proctoring.
* **Speech Analytics**: Measures clarity, confidence, speaking pace, and filler word usage.
* **Recruiter-Style PDF Report**: Includes scores, skill radar charts, timing metrics, strengths, weaknesses, and recommendations.
* **Cold Start Strategy**: Bootstrapped via LLM prompts + seed questions; improvement loop for fine-tuning.

---

## 🚀 Quick Start (PoC)

### Prerequisites

* Python 3.9+ (tested on 3.11)
* OpenAI API key with access to `gpt-4o-mini`

### Setup

1. Clone the repo:

```bash
git clone <repository-url>
cd multimodal-interview-agent
```

2. Create a virtual environment:

**Windows (PowerShell)**:

```bash
python -m venv venv
venv\Scripts\Activate.ps1
```

**macOS/Linux**:

```bash
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Configure API key (`.env`):

```env
OPENAI_API_KEY=your_openai_api_key_here
```

5. Run the Streamlit PoC:

```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

---

## 🏗️ Architecture

```
multimodal-interview-agent/
├─ app.py            # Streamlit PoC: UI, audio + webcam capture
├─ backend/          # FastAPI endpoints: evaluation, question generation, RAG, PDF
├─ utils.py          # LLM calls, TTS, evaluation, charts, PDF generation
├─ questions.py      # Seed questions per role
├─ rag_docs/         # Role-specific documents for grounding questions/evaluation
├─ requirements.txt  # Dependencies
└─ README.md
```

### Core Modules

* **`app.py`**

  * Candidate flow: resume upload, role selection, persona selection
  * Audio and webcam capture
  * Frontend timers, tab monitoring, and live feedback
* **`backend/`**

  * ASR (Whisper) transcription
  * Vision analytics (MediaPipe, FER)
  * Speech metrics extraction
  * LLM evaluation & dynamic question generation
  * RAG retrieval
* **`utils.py`**

  * `evaluate_with_llm`: Deterministic structured scoring
  * `generate_next_question`: Adaptive question generation
  * `text_to_speech_bytes`: TTS for questions
  * `skill_bar_chart_bytes`: Radar charts for report
  * `generate_pdf_report`: Recruiter-style final report

---

## 🎮 Flow

1. Candidate accepts consent & rules (audio, webcam, no cheating).
2. Upload resume and select desired role + interviewer persona.
3. AI starts interview:

   * Speaks the question via TTS
   * Candidate answers verbally
   * Backend captures audio + webcam → ASR + vision + speech metrics → LLM evaluates
4. Dynamic question progression based on candidate’s performance.
5. Optional follow-ups triggered for borderline or advanced responses.
6. Interview concludes:

   * AI speaks closing statements
   * Full PDF report generated with scores, skill charts, proctoring summary, and recommendations
   * Candidate can download the report

---

## 🤖 LLM & Agent Configuration

* **Model**: `gpt-4o-mini` (OpenAI)
* **Evaluation**: `temperature=0.0` for deterministic scoring
* **Question generation**: `temperature=0.6` for adaptive, diverse questions
* **RAG grounding**: Top-K role documents used to ensure accuracy
* **Agentic loop**: Evaluates previous answers, updates candidate phase, generates next question

---

## 🔎 Multimodal Evaluation Metrics

* **Speech Metrics**: Words per minute, filler word ratio, clarity, confidence
* **Vision Metrics**: Eye contact ratio, posture stability, emotion distribution
* **LLM Scoring**: Correctness, clarity, depth, relevance, optional follow-up suggestions
* **Proctoring**: Tab switches, prolonged face absence, suspicious background audio
* **Consistency**: Checks if answers remain logically coherent across questions

---

## 🧩 Sample Evaluation JSON

```json
{
  "score": 1..5,
  "breakdown": {
    "Correctness": 1..5,
    "Clarity": 1..5,
    "Depth": 1..5,
    "Relevance": 1..5
  },
  "feedback": "Neutral constructive feedback",
  "followup": "Optional follow-up",
  "vision_metrics": {"eye_contact":0.7,"posture":0.8},
  "speech_metrics": {"wpm":110,"filler_ratio":0.03}
}
```

---

## 📊 Sample PDF Report Includes

* Overall score & percentile
* Radar charts of skills per competency
* Strengths & weaknesses
* Speech & vision metrics summary
* Proctoring flags
* Recommendations & next steps

---

## 🔧 Customization

* Add/modify roles, personas, seed questions in `questions.py`
* Adjust evaluation prompts in `utils.py`
* Modify monitoring rules or thresholds for tab switches & webcam
* Add new RAG documents per role in `rag_docs/`

---

## ❄️ Cold Start & Improvement Loop

* **LLM-based evaluation** for initial scoring without dataset
* **Seed questions** as fallback
* **Store transcripts & evaluations** in MongoDB for future fine-tuning
* **Adaptive consistency metric** to improve question selection & evaluation

---

## 🔒 Privacy Note

* Webcam stays open only during the session; frames discarded unless opted-in
* Audio stored temporarily for processing
* Candidate can request data deletion
* LLM evaluations and PDF reports are deterministic and secure

---

## 📜 License

MIT License

---

## 🤝 Contributing

1. Fork → branch → PR → review
2. Keep contributions focused on evaluation, UI, question bank, or metrics
3. Suggest new roles, persona styles, or RAG docs


