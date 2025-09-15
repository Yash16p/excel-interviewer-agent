## 🧑‍💻 AI-Powered Excel Mock Interviewer

A Streamlit app that conducts a realistic, adaptive Excel interview. It generates questions, evaluates answers using an LLM, optionally asks follow‑ups, tracks timing, and produces a professional PDF report with a skill breakdown.

### ✨ Features

- **Adaptive interview flow**: Phase-based rounds (basic → intermediate → advanced) based on performance
- **Dynamic question count**: Typically 3–5 questions, with early end for low performance
- **LLM evaluation**: Neutral, professional scoring with multi-dimensional breakdown
- **Smart follow-ups**: Optional follow-up when score is middling (with probability gate)
- **Audio prompts**: Text-to-speech for questions, follow-ups, and outro
- **Timing analytics**: Per-question timing, averages, and total interview time
- **PDF report**: Downloadable, structured report with scores, feedback, timing and recommendations
- **Tab monitoring**: Warns on tab switch during the active interview

### 🚀 Quick Start

#### Prerequisites
- Python 3.9+ (tested with 3.11)
- OpenAI API key with access to `gpt-4o-mini`

#### Setup

1. Clone and enter the project
```bash
git clone <repository-url>
cd excel-interviewer-agent
```

2. Create and activate a virtual environment
```bash
# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure environment
Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

5. Run the app
```bash
streamlit run app.py
```
Then open `http://localhost:8501` in your browser.

### 🏗️ Architecture

```
excel-interviewer-agent/
├─ app.py            # Streamlit UI and interview flow
├─ utils.py          # LLM calls, TTS, PDF, chart utilities
├─ questions.py      # Skill areas, constants, fallback questions
├─ requirements.txt  # Python dependencies
└─ README.md         # Documentation
```

#### Core modules
- **`app.py`**: Session state, UI, timing, phase progression, follow-up flow, results, download
- **`utils.py`**:
  - `evaluate_with_llm(question, answer, ideal, memory)` — neutral scoring + feedback JSON
  - `select_next_question_api(transcript, asked_skills, avg_score)` — dynamic question generator
  - `text_to_speech_bytes(text)` — returns MP3 bytes via gTTS
  - `generate_pdf_report(candidate, transcript, overall, timings, total_duration)` — PDF bytes
  - `skill_bar_chart_bytes(skill_map)` — matplotlib PNG bytes for skill averages
  - `get_langchain_memory()` — optional conversation memory (best-effort)
- **`questions.py`**: `SKILL_AREAS`, `MIN_QUESTIONS`, `MAX_QUESTIONS`, and `FALLBACK_QUESTIONS`

### 🎮 How it works

1. Candidate reads rules and starts interview.
2. App plays a short phase intro and asks a question (with audio).
3. Candidate submits an answer; the app:
   - Times the question
   - Evaluates using the LLM (neutral JSON result)
   - May ask a follow-up if the score is middling
4. Based on average score, the app adapts phase lengths and difficulty:
   - Strong candidates advance sooner to harder questions
   - Weak performance can end after the basic phase
5. At completion, the app shows a scorecard, skill chart, timing analysis, recommendations, and a PDF download.

### 🤖 LLM configuration

- **Library**: `openai` (Responses API via Chat Completions)
- **Model**: `gpt-4o-mini`
- **Evaluation**: `temperature=0.0`, `max_tokens=400`
- **Question generation**: `temperature=0.6`, `max_tokens=300`
- **Env**: `OPENAI_API_KEY` must be set (loaded via `python-dotenv`)

### 🔎 Interview details

- **Phases**: `basic`, `intermediate`, `advanced` with dynamic lengths based on average score
- **Count**: Typically 3–5 total (see `MIN_QUESTIONS`, `MAX_QUESTIONS` and phase logic)
- **Follow-ups**:
  - Trigger when score is between 2 and 4 (inclusive)
  - Limited by `followup_limit` (default 1) and a probability gate (≈35%)
  - No follow-up for very high or very low scores
- **Skill areas**: Formulas, Pivot Tables, Data Cleaning, Productivity/Protection, Reporting
- **Timing**: Per-question timers; overall and per-question stats displayed and included in the PDF
- **Tab alerts**: Warns on `visibilitychange` during active interview

### 🧩 Evaluation output shape

```python
{
  "score": 1..5,
  "breakdown": {"Correctness": 1..5, "Efficiency": 1..5, "Clarity": 1..5, "Completeness": 1..5},
  "feedback": "<neutral, constructive sentence>",
  "followup": "<optional follow-up or empty>",
  "clarity": 1..5,
  "confidence": 1..5,
  "problem_solving": 1..5
}
```

### 🛠️ Troubleshooting

- **Missing API key**
  - Error: `EnvironmentError: Set OPENAI_API_KEY in your environment or .env file`
  - Fix: Create `.env` with a valid key and restart
- **Audio not playing**
  - gTTS requires internet; ensure connectivity
  - Click once in the page to allow audio autoplay if the browser blocks it
- **Imports failing**
  - Ensure `pip install -r requirements.txt` completed successfully
- **Charts/PDF issues**
  - Headless environments may require display backends for matplotlib; the code saves to bytes to minimize issues

### 🔧 Customization

- Tweak question difficulty/phase progression in `app.py` (`get_dynamic_phase_lengths` and flow)
- Adjust evaluation prompt and scoring defaults in `utils.py`
- Edit skill areas, min/max questions, and fallbacks in `questions.py`

### 📜 License

MIT License. See `LICENSE` if included or add one as needed.

### 🤝 Contributing

- Fork → branch → commit → PR. Please keep edits small and focused.

---

Built with Streamlit, OpenAI, gTTS, ReportLab, and matplotlib.
