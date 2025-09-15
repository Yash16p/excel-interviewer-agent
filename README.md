Got it ✅ Thanks for sharing the PDF.

Looking at your README draft and the **assignment doc**, here’s how we can **reframe your README** so it fully matches the expected deliverables and constraints:

---

# 🧑‍💻 AI-Powered Excel Mock Interviewer

A Streamlit-based Proof of Concept (PoC) that simulates a realistic Excel interview process.
The system dynamically asks questions, evaluates responses using LLMs, provides adaptive follow-ups, tracks time, and generates a structured recruiter-style feedback report (with charts + PDF).

This PoC demonstrates how an AI system can act like a **neutral interviewer**—managing the flow, evaluating, and giving structured feedback—helping organizations scale Excel skill assessments without manual effort.

---

## ✨ Features

* **Structured Interview Flow**: Multi-phase interview (basic → intermediate → advanced) with introductions, transitions, and wrap-up.
* **Adaptive Questioning**: Dynamic phase lengths—weak candidates stay longer in basics, stronger ones move faster to advanced.
* **LLM-Powered Evaluation**: Neutral, professional scoring across multiple dimensions (correctness, clarity, efficiency, completeness).
* **Smart Follow-ups**: Optional follow-ups when answers are borderline, simulating recruiter probing.
* **Recruitment Realism**: Instructions & agreement modal, tab-change alerts, live timers per question, webcam widget.
* **Audio Prompts (TTS)**: Interviewer automatically speaks introductions, questions, follow-ups, and closing.
* **Timing Analytics**: Tracks time per question, averages, and overall interview duration.
* **Consistency Metric**: Checks if answers remain logically consistent across phases.
* **PDF Report**: Full recruiter-style scorecard with charts, timing analysis, strengths, weaknesses, recommendations.
* **Tab Monitoring**: Alerts on tab-switching (cheating detection).
* **Webcam Monitoring**: Persistent widget to simulate proctoring (no storage).

---

## 🚀 Quick Start

### Prerequisites

* Python 3.9+ (tested on 3.11)
* OpenAI API key with access to `gpt-4o-mini`

### Setup

1. Clone the repo:

   ```bash
   git clone <repository-url>
   cd excel-interviewer-agent
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

4. Configure API key (`.env` file):

   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

5. Run the app:

   ```bash
   streamlit run app.py
   ```

   Open [http://localhost:8501](http://localhost:8501).

---

## 🏗️ Architecture

```
excel-interviewer-agent/
├─ app.py            # Main Streamlit app: interview flow & UI
├─ utils.py          # LLM calls, evaluation, TTS, PDF, charts
├─ questions.py      # Skill areas, constants, fallback Qs
├─ requirements.txt  # Dependencies
└─ README.md         # Documentation
```

### Core Modules

* **`app.py`**

  * Session state & flow (idle → basic → intermediate → advanced → done)
  * Timing, tab monitoring, follow-ups, structured output
  * Webcam widget in sidebar
* **`utils.py`**

  * `evaluate_with_llm`: Structured scoring & feedback
  * `select_next_question_api`: Adaptive question generator
  * `text_to_speech_bytes`: Audio prompts
  * `skill_bar_chart_bytes`: Skill visualization
  * `generate_pdf_report`: Recruiter-style PDF
  * `get_langchain_memory`: Optional interview memory
* **`questions.py`**

  * Defines `SKILL_AREAS`, `MIN_QUESTIONS`, `MAX_QUESTIONS`
  * Provides fallback Qs

---

## 🎮 Flow

1. Candidate accepts rules (no external help, timed, tab-monitoring).
2. App plays intro → begins **basic phase**.
3. Candidate answers; LLM evaluates:

   * If strong → progress faster
   * If weak → stay longer in basics
   * If average → balanced flow
4. Optional **follow-up** triggered for borderline scores.
5. Intermediate & advanced phases proceed similarly.
6. At completion:

   * Outro spoken by AI
   * Recruiter-style feedback: scorecard, timing analysis, consistency, strengths/weaknesses, recommendations
   * Candidate downloads PDF report.

---

## 🤖 LLM Configuration

* **Library**: `openai` (Chat Completions)
* **Model**: `gpt-4o-mini`
* **Evaluation**: `temperature=0.0`, deterministic scoring
* **Question generation**: `temperature=0.6`, diverse but relevant
* **Env**: `OPENAI_API_KEY` via `dotenv`

---

## 🔎 Interview Mechanics

* **Phases**: Basic → Intermediate → Advanced
* **Dynamic lengths**:

  * High performers → faster to advanced
  * Weak → stay longer in basics
* **Follow-ups**:

  * Only if score ∈ \[2,4]
  * Probability \~35%
  * Limit = 1 follow-up
* **Skill areas**: Formulas, PivotTables, Data Cleaning, Reporting, Protection
* **Consistency check**: Flags contradictory answers
* **Timing**:

  * Live timer per Q
  * Avg/fastest/slowest in feedback
* **Monitoring**:

  * Tab-switch alerts
  * Webcam active (no storage)

---

## 🧩 Evaluation Output (JSON)

```json
{
  "score": 1..5,
  "breakdown": {
    "Correctness": 1..5,
    "Efficiency": 1..5,
    "Clarity": 1..5,
    "Completeness": 1..5
  },
  "feedback": "Neutral constructive feedback",
  "followup": "Optional follow-up",
  "clarity": 1..5,
  "confidence": 1..5,
  "problem_solving": 1..5
}
```

---

## 📊 Sample Output

* Overall Score: `3.7/5`
* Strengths: PivotTables, Reporting
* Weaknesses: Data Cleaning
* Avg clarity: `3.5/5`
* Avg confidence: `3.2/5`
* Avg problem-solving: `3.8/5`
* Recommendations: Practice Power Query, explain thought process step by step

---

## 🔧 Customization

* Tweak phase lengths in `get_dynamic_phase_lengths`
* Adjust evaluation prompt in `utils.py`
* Add/modify fallback questions in `questions.py`
* Change monitoring rules (tab/warning strictness)

---

## ❄️ Cold Start Strategy

Since no dataset exists, system bootstraps via:

* **LLM-based evaluation**: Uses GPT to simulate interviewer scoring.
* **Fallback Qs**: Handcrafted seed set in `questions.py`.
* **Improvement Loop**: Store transcripts + scores for future fine-tuning.
* **Consistency Metric**: Adds data signals to improve evaluations.

---

## 🔒 Privacy Note

* Webcam stays open only during session, never stored.
* PDFs may include webcam thumbnails (configurable).
* Candidate data is session-local unless recruiter exports PDF.

---

## 📜 License

MIT License

---

## 🤝 Contributing

Fork → branch → PR → review.
Keep contributions focused (evaluation, UI, question bank, etc).

---

👉 This README now fully aligns with your **assignment doc** (structured flow, evaluation, agentic behavior, report, constraints).

Would you like me to also **add some sample transcripts** (Expected Deliverable #2) that demonstrate the system’s behavior, so your submission is stronger?
