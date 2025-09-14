# app.py
import streamlit as st
import json
from datetime import datetime
from utils import (
    evaluate_with_llm,
    generate_pdf_report,
    get_langchain_memory,
    select_next_question_api,
    text_to_speech
)
from questions import MIN_QUESTIONS, MAX_QUESTIONS

# --- State Init ---
if "transcript" not in st.session_state: st.session_state.transcript = []
if "asked_skills" not in st.session_state: st.session_state.asked_skills = []
if "candidate_name" not in st.session_state: st.session_state.candidate_name = ""
if "memory" not in st.session_state: st.session_state.memory = get_langchain_memory()
if "interview_complete" not in st.session_state: st.session_state.interview_complete = False
if "current_question" not in st.session_state: st.session_state.current_question = None
if "intro_shown" not in st.session_state: st.session_state.intro_shown = False
if "followup_mode" not in st.session_state: st.session_state.followup_mode = False
if "followup_count" not in st.session_state: st.session_state.followup_count = 0

st.set_page_config(page_title="AI Excel Interviewer", layout="centered")
st.title("🧑‍💻 AI-Powered Excel Mock Interviewer")

st.session_state.candidate_name = st.text_input(
    "Candidate Name (optional):", st.session_state.candidate_name
)

# --- Start Interview ---
if st.button("🚀 Start Interview") and not st.session_state.current_question:
    st.session_state.transcript = []
    st.session_state.asked_skills = []
    st.session_state.interview_complete = False
    st.session_state.current_question = select_next_question_api([], [], None)
    st.session_state.intro_shown = False
    st.session_state.followup_mode = False
    st.session_state.followup_count = 0
    st.rerun()

# --- Interview Flow ---
if st.session_state.current_question and not st.session_state.interview_complete:
    if not st.session_state.intro_shown and len(st.session_state.transcript) == 0:
        intro = f"Hi {st.session_state.candidate_name or 'there'}, I’m your AI Excel Interviewer. Let's start with some questions."
        st.info(intro)
        st.audio(text_to_speech(intro), format="audio/mp3")
        st.session_state.intro_shown = True

    q = st.session_state.current_question
    q_number = len(st.session_state.transcript) + 1

    st.subheader(f" Q{q_number} ({q['skill_area']}, {q['level']}):")
    st.write(q["question"])
    st.audio(text_to_speech(q["question"], filename=f"q{q_number}.mp3"), format="audio/mp3")

    candidate_answer = st.text_area("Your Answer:", key=f"ans_{q_number}_{q['id']}")

    if st.button("Submit Answer", key=f"submit_{q_number}_{q['id']}"):
        evaluation = evaluate_with_llm(q["question"], candidate_answer, q.get("ideal", "N/A"), st.session_state.memory)

        st.session_state.transcript.append({
            "question": q["question"],
            "answer": candidate_answer,
            "evaluation": evaluation,
            "skill_area": q["skill_area"]
        })
        st.session_state.asked_skills.append(q["skill_area"])

        # Store feedback for later display (no immediate feedback shown)
        feedback = f"On that answer, I'd rate you {evaluation['score']}/5. {evaluation['feedback']}"
        recommendation = "Keep practicing Excel basics." if evaluation['score'] <= 2 else "Great job! Try pushing into advanced cases."

        # Follow-up mode: ask one clarifying Q before moving on only if score is good but not perfect (3-4/5)
        # No follow-up for very low scores (1-2/5) or "don't know" answers
        if 3 <= evaluation['score'] <= 4 and st.session_state.followup_count < 2:
            st.session_state.followup_mode = True
            st.session_state.followup_question = f"Could you walk me through your approach in more detail for that last answer?"
            st.session_state.followup_answer = ""
            st.session_state.followup_count += 1
            st.rerun()
        else:
            # If perfect score, move to next question directly
            # Progress logic
            answered_count = len(st.session_state.transcript)
            scores = [t["evaluation"]["score"] for t in st.session_state.transcript]
            avg_score = sum(scores) / len(scores) if scores else None

            # End interview after exactly 4 questions
            if answered_count >= MAX_QUESTIONS:
                st.session_state.interview_complete = True
                st.session_state.current_question = None

            if not st.session_state.interview_complete:
                st.session_state.current_question = select_next_question_api(
                    st.session_state.transcript,
                    st.session_state.asked_skills,
                    avg_score
                )
            st.rerun()

# --- Follow-up Mode ---
if st.session_state.get("followup_mode"):
    st.subheader("🔎 Follow-up:")
    st.write(st.session_state.followup_question)
    st.audio(text_to_speech(st.session_state.followup_question, filename="followup.mp3"), format="audio/mp3")

    follow_ans = st.text_area("Your Follow-up Answer:", key=f"followup_{len(st.session_state.transcript)}")
    if st.button("Submit Follow-up"):
        st.session_state.followup_mode = False

        # Progress logic
        answered_count = len(st.session_state.transcript)
        scores = [t["evaluation"]["score"] for t in st.session_state.transcript]
        avg_score = sum(scores) / len(scores) if scores else None

        # End interview after exactly 4 questions
        if answered_count >= MAX_QUESTIONS:
            st.session_state.interview_complete = True
            st.session_state.current_question = None

        if not st.session_state.interview_complete:
            st.session_state.current_question = select_next_question_api(
                st.session_state.transcript,
                st.session_state.asked_skills,
                avg_score
            )
        st.rerun()

# --- Interview Complete ---
if st.session_state.interview_complete:
    outro = f"Great job {st.session_state.candidate_name or 'Candidate'}! That concludes our mock interview. Here are your results."
    st.success(outro)
    st.audio(text_to_speech(outro, filename="outro.mp3"), format="audio/mp3")

    scores = [t["evaluation"]["score"] for t in st.session_state.transcript]
    overall_score = sum(scores) / len(scores) if scores else 0
    st.metric("Overall Score", f"{overall_score:.2f}/5")

    st.subheader("📊 Skill Area Breakdown")
    skill_scores = {}
    for t in st.session_state.transcript:
        skill_scores.setdefault(t["skill_area"], []).append(t["evaluation"]["score"])
    for sa, vals in skill_scores.items():
        st.write(f"{sa}: {sum(vals)/len(vals):.2f}/5")

    st.subheader("📝 Transcript")
    for i, t in enumerate(st.session_state.transcript, 1):
        st.markdown(f"**Q{i} ({t['skill_area']})**: {t['question']}")
        st.markdown(f"**Answer:** {t['answer']}")
        st.markdown(f"**Score:** {t['evaluation']['score']}/5")
        st.markdown(f"**Feedback:** {t['evaluation']['feedback']}")

    pdf_bytes = generate_pdf_report(
        st.session_state.candidate_name,
        st.session_state.transcript,
        overall_score
    )
    st.download_button(
        "⬇️ Download PDF Report",
        data=pdf_bytes,
        file_name=f"{st.session_state.candidate_name or 'candidate'}_feedback.pdf",
        mime="application/pdf"
    )

    if st.button("🔄 Restart"):
        for k in ["transcript","asked_skills","interview_complete","current_question","intro_shown","followup_mode","followup_count"]:
            st.session_state[k] = [] if isinstance(st.session_state[k], list) else False if isinstance(st.session_state[k], bool) else 0
        st.rerun()
