import streamlit as st
import random
import time
from datetime import datetime

# Utility functions
def get_avg_score():
    scores = [t["evaluation"]["score"] for t in st.session_state.transcript if "evaluation" in t]
    if not scores:
        return None
    return sum(scores)/len(scores)

# Lazy imports - only import when needed
def get_utils():
    if 'utils_imported' not in st.session_state:
        with st.spinner("Loading interview system..."):
            from utils import (
                evaluate_with_llm,
                generate_pdf_report,
                get_langchain_memory,
                select_next_question_api,
                text_to_speech_bytes,
                skill_bar_chart_bytes
            )
            st.session_state.utils_imported = {
                'evaluate_with_llm': evaluate_with_llm,
                'generate_pdf_report': generate_pdf_report,
                'get_langchain_memory': get_langchain_memory,
                'select_next_question_api': select_next_question_api,
                'text_to_speech_bytes': text_to_speech_bytes,
                'skill_bar_chart_bytes': skill_bar_chart_bytes
            }
    return st.session_state.utils_imported

def get_questions():
    if 'questions_imported' not in st.session_state:
        from questions import MIN_QUESTIONS, MAX_QUESTIONS, SKILL_AREAS
        st.session_state.questions_imported = {
            'MIN_QUESTIONS': MIN_QUESTIONS,
            'MAX_QUESTIONS': MAX_QUESTIONS,
            'SKILL_AREAS': SKILL_AREAS
        }
    return st.session_state.questions_imported

def get_memory():
    if st.session_state.memory is None:
        utils = get_utils()
        st.session_state.memory = utils['get_langchain_memory']()
    return st.session_state.memory

# --- Session init ---
if "phase" not in st.session_state:
    st.session_state.phase = "idle"  # idle, basic, intermediate, advanced, done
if "transcript" not in st.session_state:
    st.session_state.transcript = []
if "asked_skills" not in st.session_state:
    st.session_state.asked_skills = []
if "candidate_name" not in st.session_state:
    st.session_state.candidate_name = ""
if "memory" not in st.session_state:
    st.session_state.memory = None  # Will be initialized when needed
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "intro_played" not in st.session_state:
    st.session_state.intro_played = False
if "followup_pending" not in st.session_state:
    st.session_state.followup_pending = False
if "followup_text" not in st.session_state:
    st.session_state.followup_text = ""
if "followup_limit" not in st.session_state:
    st.session_state.followup_limit = 1
if "timings" not in st.session_state:
    st.session_state.timings = []  # seconds per question
if "question_start" not in st.session_state:
    st.session_state.question_start = None
if "interview_start" not in st.session_state:
    st.session_state.interview_start = None
if "show_instructions" not in st.session_state:
    st.session_state.show_instructions = False

st.set_page_config(page_title="AI-Powered Excel Mock Interviewer", layout="centered")
st.title("🧑‍💻 AI-Powered Excel Mock Interviewer (Recruiter-style PoC)")

# Quick loading optimization - defer heavy operations
if not st.session_state.get('app_loaded', False):
    with st.spinner("🚀 Loading interview system..."):
        time.sleep(0.3)  # Brief loading indicator
    st.session_state.app_loaded = True

# Candidate name & instructions
st.sidebar.header("Instructions")
st.sidebar.markdown("""
- This is a timed, adaptive mock interview (text answers).
- The interviewer will speak each question automatically (browser may require first interaction).
- Do not switch tabs or try to navigate away — a warning will appear.
- Final feedback (scorecard + PDF) is shown at the end.
""")
st.sidebar.markdown("**Tech note:** If audio doesn't autoplay, click on the page once to enable audio playback in your browser.")

st.session_state.candidate_name = st.text_input("Candidate Name (optional):", st.session_state.candidate_name)

# Instructions & Agreement Modal
if st.session_state.phase == "idle":
    st.markdown("## 📋 Interview Instructions & Agreement")
    st.markdown("""
    **This is a professional Excel skills assessment with the following rules:**
    
    - ⏱️ **Timed Interview**: Each question has a time limit for realistic assessment
    - 🚫 **No External Help**: Use only your knowledge - no Google, books, or assistance
    - 📱 **Tab Monitoring**: Tab switching is tracked and reported to recruiters
    - 🎯 **Adaptive Difficulty**: Questions adjust based on your performance
    - 📊 **Professional Assessment**: Results include timing analysis and skill breakdown
    
    **By proceeding, you agree to follow these guidelines.**
    """)
    
    agree = st.checkbox("✅ I agree to the interview rules and will not use external assistance", key="agree_checkbox")
    
    if not agree:
        st.warning("⚠️ Please check the agreement box to proceed with the interview.")

# Interview progress tracking
if not st.session_state.get("interview_complete", False) and st.session_state.phase != "idle":
    st.markdown("---")
    st.markdown("### 📊 Interview Progress")
    
    # Show current interview status
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.metric("Questions Answered", len(st.session_state.transcript))
    with col2:
        st.metric("Current Phase", st.session_state.phase.title())
    with col3:
        if st.session_state.question_start:
            elapsed = int(time.time() - st.session_state.question_start)
            st.metric("Time on Current Question", f"{elapsed}s")
    
    st.markdown("---")

# Start interview button (requires agreement)
if st.session_state.phase == "idle":
    agree = st.session_state.get("agree_checkbox", False)
    if st.button("🚀 Start Interview", disabled=not agree):
        if agree:
            st.session_state.phase = "basic"
            st.session_state.transcript = []
            st.session_state.asked_skills = []
            st.session_state.current_question = None
            st.session_state.intro_played = False
            st.session_state.followup_pending = False
            st.session_state.followup_text = ""
            st.session_state.followup_limit = 1
            st.session_state.timings = []
            st.session_state.question_start = None
            st.session_state.interview_start = time.time()  # Record interview start time
        st.rerun()


# Dynamic phase length calculation based on performance
def get_dynamic_phase_lengths(avg_score):
    """Calculate phase lengths based on candidate performance"""
    if avg_score is None:
        # No data yet, use default lengths
        return {"basic": 2, "intermediate": 2, "advanced": 0}
    
    if avg_score >= 4.0:
        # Strong candidate: shorter basic, more advanced
        return {"basic": 1, "intermediate": 2, "advanced": 1}
    elif avg_score <= 2.0:
        # Very weak candidate: stay in basics only, no advancement
        return {"basic": 4, "intermediate": 0, "advanced": 0}
    elif avg_score <= 2.5:
        # Weak candidate: mostly basics, minimal intermediate
        return {"basic": 3, "intermediate": 1, "advanced": 0}
    else:
        # Average candidate: balanced approach
        return {"basic": 2, "intermediate": 2, "advanced": 0}

# Play bytes audio in streamlit: st.audio accepts bytes
def play_audio_now(text):
    utils = get_utils()
    audio_bytes = utils['text_to_speech_bytes'](text)
    if audio_bytes:
        st.audio(audio_bytes, format="audio/mp3")

# Phase handler with dynamic question selection
def ensure_question_for_phase(phase):
    # If there is currently no current_question, generate one for this phase
    if st.session_state.current_question is None:
        avg = get_avg_score()
        # Enhanced question selection based on performance
        utils = get_utils()
        q = utils['select_next_question_api'](st.session_state.transcript, st.session_state.asked_skills, avg)
        # Start timing for this question
        st.session_state.question_start = time.time()
        st.session_state.current_question = q

# Main interview loop UI
if st.session_state.phase in ("basic", "intermediate", "advanced") and not st.session_state.followup_pending:
    # Play intro to phase (once)
    if not st.session_state.intro_played:
        if st.session_state.phase == "basic":
            intro_text = f"Hello {st.session_state.candidate_name or 'candidate'}. We'll start with the basic round to check core Excel skills."
        elif st.session_state.phase == "intermediate":
            intro_text = "Next, we will move into intermediate-level Excel skills focusing on data cleaning and lookups."
        else:
            intro_text = "Now moving into advanced Excel topics like pivot tables and reporting."
        # play TTS (best-effort autoplay - browser may require click)
        play_audio_now(intro_text)
        st.session_state.intro_played = True
        st.write(intro_text)

    # ensure a question is present
    ensure_question_for_phase(st.session_state.phase)
    q = st.session_state.current_question
    q_no = len(st.session_state.transcript) + 1
    
    # Live timer display
    if st.session_state.question_start:
        elapsed = time.time() - st.session_state.question_start
        st.markdown(f"⏱️ **Time elapsed for this question: {int(elapsed)} seconds**")
    
    st.markdown(f"### Q{q_no} — ({q.get('skill_area','')}, {q.get('level','')})")
    st.write(q["question"])
    play_audio_now(q["question"])

    # user answer UI (unique key)
    ans_key = f"ans_{q_no}_{q['id']}"
    user_answer = st.text_area("Your answer:", key=ans_key, height=160)

    if st.button("Submit Answer", key=f"submit_{q_no}_{q['id']}"):
        # Record timing for this question
        if st.session_state.question_start:
            elapsed = time.time() - st.session_state.question_start
            st.session_state.timings.append(elapsed)
            st.session_state.question_start = None
        
        # evaluate (store evaluation but do not show score)
        utils = get_utils()
        memory = get_memory()
        ev = utils['evaluate_with_llm'](q["question"], user_answer, q.get("ideal",""), memory=memory)
        # store
        st.session_state.transcript.append({
            "question": q["question"],
            "answer": user_answer,
            "evaluation": ev,
            "skill_area": q.get("skill_area","General"),
            "id": q.get("id"),
            "time_taken": st.session_state.timings[-1] if st.session_state.timings else 0
        })
        st.session_state.asked_skills.append(q.get("skill_area","General"))
        # Decide if follow-up is needed: if score between 2 and 4 (inclusive) and followup_limit not exceeded
        score = ev.get("score",3)
        need_follow = (2 <= score <= 4) and (st.session_state.followup_limit > 0)
        # probability gate to avoid always-followup
        if need_follow and random.random() < 0.35 and ev.get("followup"):
            st.session_state.followup_pending = True
            st.session_state.followup_text = ev.get("followup") or "Could you explain your approach in more detail?"
            st.session_state.followup_limit -= 1
            # play followup audio
            play_audio_now(st.session_state.followup_text)
        else:
            st.session_state.followup_pending = False
            st.session_state.followup_text = ""
            # Dynamic phase progression based on performance
            answered = len(st.session_state.transcript)
            avg = get_avg_score()
            phase_lengths = get_dynamic_phase_lengths(avg)
            
            if st.session_state.phase == "basic":
                # Only advance if candidate has answered enough questions AND has good performance
                if answered >= phase_lengths["basic"] and (avg is None or avg >= 3.0):
                    st.session_state.phase = "intermediate"
                    st.session_state.current_question = None
                    st.session_state.intro_played = False
                elif answered >= phase_lengths["basic"] and avg is not None and avg < 3.0:
                    # Weak candidate - end interview after basic phase
                    st.session_state.phase = "done"
                    st.session_state.interview_complete = True
                    st.session_state.current_question = None
                    # Store reason for ending early
                    st.session_state.early_end_reason = f"Interview ended after basic phase due to low performance (avg: {avg:.1f}/5.0). Focus on improving fundamental Excel skills."
                else:
                    st.session_state.current_question = None
            elif st.session_state.phase == "intermediate":
                if answered >= phase_lengths["basic"] + phase_lengths["intermediate"]:
                    # Only advance to advanced if performance is good enough
                    if phase_lengths["advanced"] > 0 and (avg is None or avg >= 3.5):
                        st.session_state.phase = "advanced"
                        st.session_state.current_question = None
                        st.session_state.intro_played = False
                    else:
                        # End interview if no advanced phase or performance not good enough
                        st.session_state.phase = "done"
                        st.session_state.interview_complete = True
                        st.session_state.current_question = None
                        
                        # Stop tab detection alerts
                        st.components.v1.html("""
                        <script>
                        window.interviewComplete = true;
                        </script>
                        """, height=0)
                else:
                    st.session_state.current_question = None
            elif st.session_state.phase == "advanced":
                # Advanced phase: end after required questions
                total_questions = phase_lengths["basic"] + phase_lengths["intermediate"] + phase_lengths["advanced"]
                questions = get_questions()
                if answered >= total_questions or answered >= questions['MAX_QUESTIONS']:
                    st.session_state.phase = "done"
                    st.session_state.interview_complete = True
                    st.session_state.current_question = None
                    
                    # Stop tab detection alerts
                    st.components.v1.html("""
                    <script>
                    window.interviewComplete = true;
                    </script>
                    """, height=0)
                else:
                    st.session_state.current_question = None
        st.rerun()

# --- Follow-up UI (only shown when followup_pending is True) ---
if st.session_state.get("followup_pending"):
    st.markdown("### 🔎 Follow-up question")
    st.write(st.session_state.followup_text)
    play_audio_now(st.session_state.followup_text)
    fu_key = f"followup_{len(st.session_state.transcript)}"
    fu_answer = st.text_area("Your brief follow-up answer:", key=fu_key, height=120)
    if st.button("Submit Follow-up", key=f"submit_followup_{fu_key}"):
        # attach followup answer to last transcript item
        if st.session_state.transcript:
            st.session_state.transcript[-1]["followup_answer"] = fu_answer
        st.session_state.followup_pending = False
        st.session_state.followup_text = ""
        st.rerun()

# --- If interview completed: show recruiters-style feedback and charts ---
if st.session_state.get("interview_complete"):
    outro_text = f"Thank you {st.session_state.candidate_name or 'candidate'}. That concludes the interview. I will now share a structured feedback summary."
    st.success(outro_text)
    play_audio_now(outro_text)

    # compute metrics
    transcript = st.session_state.transcript
    scores = [t["evaluation"].get("score",3) for t in transcript]
    overall = sum(scores)/len(scores) if scores else 0

    # Build skill map
    skill_map = {}
    clarity_vals = []
    confidence_vals = []
    problem_vals = []
    for t in transcript:
        sa = t.get("skill_area","General")
        skill_map.setdefault(sa, []).append(t["evaluation"].get("score",3))
        clarity_vals.append(t["evaluation"].get("clarity",3))
        confidence_vals.append(t["evaluation"].get("confidence",3))
        problem_vals.append(t["evaluation"].get("problem_solving",3))

    # Calculate total interview duration
    total_duration = 0
    if st.session_state.interview_start:
        total_duration = time.time() - st.session_state.interview_start
    
    st.header("📊 Scorecard")
    
    # Show early end reason if applicable
    if st.session_state.get("early_end_reason"):
        st.warning(f"⚠️ **{st.session_state.early_end_reason}**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall score", f"{overall:.2f}/5")
    with col2:
        st.metric("Total interview time", f"{int(total_duration//60)}m {int(total_duration%60)}s")
    with col3:
        avg_time = sum(st.session_state.timings) / len(st.session_state.timings) if st.session_state.timings else 0
        st.metric("Avg time per question", f"{avg_time:.1f}s")

    # Skill bar chart
    utils = get_utils()
    chart_bytes = utils['skill_bar_chart_bytes'](skill_map)
    st.image(chart_bytes, use_container_width=True)

    # Strengths & Weaknesses
    st.subheader("💡 Strengths & Weaknesses")
    strengths = [k for k,v in skill_map.items() if sum(v)/len(v) >= 4]
    weaknesses = [k for k,v in skill_map.items() if sum(v)/len(v) <= 2.5]
    if strengths:
        st.success("Strengths: " + ", ".join(strengths))
    if weaknesses:
        st.error("Weaknesses: " + ", ".join(weaknesses))
    if not strengths and not weaknesses:
        st.info("Balanced performance across skill areas.")

    # Behavioral metrics
    st.subheader("🧭 Communication & Problem Solving")
    st.write(f"Average clarity: {sum(clarity_vals)/len(clarity_vals):.2f}/5")
    st.write(f"Average perceived confidence: {sum(confidence_vals)/len(confidence_vals):.2f}/5")
    st.write(f"Average problem-solving rating: {sum(problem_vals)/len(problem_vals):.2f}/5")

    # Detailed transcript with feedback and timing
    st.subheader("📝 Detailed Transcript & Feedback")
    for i, t in enumerate(transcript, 1):
        st.markdown(f"**Q{i} ({t.get('skill_area','')})**: {t['question']}")
        st.markdown(f"- **Your answer:** {t.get('answer','')}")
        ev = t.get("evaluation", {})
        st.markdown(f"- **Score:** {ev.get('score','N/A')}/5")
        st.markdown(f"- **Time taken:** {int(t.get('time_taken', 0))} seconds")
        st.markdown(f"- **Feedback:** {ev.get('feedback','')}")
        if t.get("followup_answer"):
            st.markdown(f"- **Follow-up answer:** {t.get('followup_answer')}")
        st.markdown("---")
    
    # Timing analysis
    st.subheader("⏱️ Timing Analysis")
    if st.session_state.timings:
        avg_time = sum(st.session_state.timings) / len(st.session_state.timings)
        st.write(f"Average time per question: {avg_time:.1f} seconds")
        st.write(f"Fastest question: {min(st.session_state.timings):.1f} seconds")
        st.write(f"Slowest question: {max(st.session_state.timings):.1f} seconds")
    else:
        st.write("No timing data available.")

    # Recommendation text (personalized)
    st.subheader("📝 Recommendations & Next Steps")
    recs = []
    if weaknesses:
        recs.append("Focus on: " + ", ".join(weaknesses))
    else:
        recs.append("Continue to strengthen advanced reporting & performance optimization skills.")
    recs.append("Practice real datasets with PivotTables and Power Query.")
    recs.append("Work on communicating approach step-by-step during answers.")
    for r in recs:
        st.write("- " + r)

    # Download PDF with timing information
    utils = get_utils()
    pdf = utils['generate_pdf_report'](
        st.session_state.candidate_name,
        transcript, 
        overall,
        timings=st.session_state.timings,
        total_duration=total_duration
    )
    st.download_button("⬇️ Download full interview report (PDF)", data=pdf, file_name=f"{st.session_state.candidate_name or 'candidate'}_interview_report.pdf", mime="application/pdf")

    # restart
    if st.button("🔄 Start new interview"):
        keys_to_clear = [
            "phase", "transcript", "asked_skills", "current_question", "intro_played",
            "followup_pending", "followup_text", "followup_limit", "interview_complete",
            "timings", "question_start", "interview_start", "show_instructions"
        ]
        for k in keys_to_clear:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()