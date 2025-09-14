# app.py
import streamlit as st
import random
import time
from datetime import datetime

from utils import (
    evaluate_with_llm,
    generate_pdf_report,
    get_langchain_memory,
    select_next_question_api,
    text_to_speech_bytes,
    skill_bar_chart_bytes,
    compute_consistency
)
from questions import MIN_QUESTIONS, MAX_QUESTIONS, SKILL_AREAS
from ui_helpers import show_instructions_modal, tab_detection_component

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
    st.session_state.memory = get_langchain_memory()
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
if "tab_change_count" not in st.session_state:
    st.session_state.tab_change_count = 0
if "timings" not in st.session_state:
    st.session_state.timings = []   # seconds per question
if "question_start" not in st.session_state:
    st.session_state.question_start = None
if "audio_allowed" not in st.session_state:
    st.session_state.audio_allowed = False  # we ask user to click once to allow autoplay if browser blocks

st.set_page_config(page_title="AI-Powered Excel Mock Interviewer", layout="centered")
st.title("🧑‍💻 AI-Powered Excel Mock Interviewer — Full Recruitment Flow (PoC)")

# Sidebar instructions & agreement
st.sidebar.header("Before you start")
st.sidebar.write("Read instructions, enable audio if blocked, and start the interview when ready.")
if st.sidebar.button("Show Instructions"):
    show_instructions_modal()

st.session_state.candidate_name = st.text_input("Candidate Name (optional):", st.session_state.candidate_name)

# Tab detection: expose a hidden number input to be updated by JS (see ui_helpers)
if not st.session_state.get("interview_complete", False):
    # Create a truly hidden input using HTML component
    st.components.v1.html(f"""
    <input type="number" id="hidden_tab_count" value="{st.session_state.tab_change_count}" style="display: none;" />
    <script>
    let tabChangeCount = {st.session_state.tab_change_count};
    document.addEventListener('visibilitychange', function() {{
        if (document.hidden && !window.interviewComplete) {{
            tabChangeCount++;
            alert("Attention: You switched tabs or minimized the window. Please return to the interview. This event may be recorded by the interviewer. Tab changes: " + tabChangeCount);
            // Update the hidden input
            const input = document.getElementById('hidden_tab_count');
            if (input) {{
                input.value = tabChangeCount;
                // Trigger a custom event to notify Streamlit
                input.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }}
        }}
    }});
    </script>
    """, height=0)
    
    # Check for updates (this won't work perfectly, but it's better than showing the input)
    # We'll use a different approach - track in session state directly

# Start interview flow: require agreement checkbox
if st.session_state.phase == "idle":
    st.markdown("## Ready to begin?")
    st.write("Click **Start Interview** when you're ready. You may need to click once to enable audio playback in your browser.")
    
    # Agreement checkbox
    st.markdown("### 📋 Interview Agreement")
    agree = st.checkbox("✅ I agree to follow the interview rules: This mock interview is timed and adaptive. I will not use external aids and understand that tab switching will be recorded.", key="agree_checkbox")
    
    if not agree:
        st.warning("⚠️ Please check the agreement box above to enable the Start Interview button.")
    
    if st.button("Start Interview", disabled=not agree):
        if agree:
            st.session_state.phase = "basic"
            st.session_state.transcript = []
            st.session_state.asked_skills = []
            st.session_state.current_question = None
            st.session_state.intro_played = False
            st.session_state.followup_pending = False
            st.session_state.followup_text = ""
            st.session_state.followup_limit = 1
            st.session_state.tab_change_count = 0
            st.session_state.timings = []
            st.session_state.question_start = None
            st.session_state.audio_allowed = True  # user clicked so audio usually allowed
    st.rerun()

# helper: play audio bytes inline
def play_audio_now(text):
    audio_bytes = text_to_speech_bytes(text)
    if audio_bytes:
        st.audio(audio_bytes, format="audio/mp3")

# Compute average score
def get_avg_score():
    scores = [t["evaluation"]["score"] for t in st.session_state.transcript if "evaluation" in t]
    if not scores:
        return None
    return sum(scores)/len(scores)

# ensure question generator
def ensure_question_for_phase(phase):
    if st.session_state.current_question is None:
        avg = get_avg_score()
        q = select_next_question_api(st.session_state.transcript, st.session_state.asked_skills, avg)
        st.session_state.current_question = q
        st.session_state.question_start = time.time()

# Phase lengths dynamic: function returning desired counts for basic/intermediate
def phase_length_plan(avg_score):
    # base plan: basic=2, intermediate=2, advanced=rest
    basic = 2
    intermediate = 2
    # adjust: strong -> shorter basic; weak -> longer basic
    if avg_score is None:
        return basic, intermediate
    if avg_score >= 4.5:
        return max(1, basic-1), intermediate  # strong, shorter basic
    if avg_score <= 2.0:
        return basic+1, intermediate  # weak, longer basic
    # mixed: default
    return basic, intermediate

# Main loop: phases
if st.session_state.phase in ("basic","intermediate","advanced") and not st.session_state.followup_pending:
    # phase intro once
    if not st.session_state.intro_played:
        if st.session_state.phase == "basic":
            intro_text = f"Hello {st.session_state.candidate_name or 'candidate'}. We'll begin with the basic round to assess core Excel skills."
        elif st.session_state.phase == "intermediate":
            intro_text = "Next, we'll move into intermediate Excel tasks focusing on data cleaning and lookups."
        else:
            intro_text = "Now we'll proceed to the advanced round covering pivot tables and reporting."
        if st.session_state.audio_allowed:
            play_audio_now(intro_text)
        st.info(intro_text)
        st.session_state.intro_played = True

    ensure_question_for_phase(st.session_state.phase)
    q = st.session_state.current_question
    q_no = len(st.session_state.transcript) + 1

    st.markdown(f"### Q{q_no} — ({q.get('skill_area','')}, {q.get('level','')})")
    st.write(q["question"])
    if st.session_state.audio_allowed:
        play_audio_now(q["question"])

    # show live small timer next to submit button
    # start timer
    if st.session_state.question_start is None:
        st.session_state.question_start = time.time()

    # user answer box
    ans_key = f"ans_{q_no}_{q['id']}"
    user_answer = st.text_area("Your answer:", key=ans_key, height=160)

    # Submit action
    if st.button("Submit Answer", key=f"submit_{q_no}_{q['id']}"):
        # record timing
        if st.session_state.question_start:
            elapsed = time.time() - st.session_state.question_start
        else:
            elapsed = 0
        st.session_state.timings.append(elapsed)
        st.session_state.question_start = None

        ev = evaluate_with_llm(q["question"], user_answer, q.get("ideal",""), memory=st.session_state.memory)
        st.session_state.transcript.append({
            "question": q["question"],
            "answer": user_answer,
            "evaluation": ev,
            "skill_area": q.get("skill_area","General"),
            "id": q.get("id")
        })
        st.session_state.asked_skills.append(q.get("skill_area","General"))

        # follow-up decision: only when score in 2..4 and followup_limit left AND LLM suggested followup (ev['followup'])
        score = ev.get("score",3)
        suggested_followup = ev.get("followup","").strip()
        need_follow = (2 <= score <= 4) and (st.session_state.followup_limit > 0) and bool(suggested_followup)
        if need_follow and random.random() < 0.35:
            st.session_state.followup_pending = True
            st.session_state.followup_text = suggested_followup
            st.session_state.followup_limit -= 1
            if st.session_state.audio_allowed:
                play_audio_now(st.session_state.followup_text)
            # do not change question_now here; follow-up is handled next
        else:
            st.session_state.followup_pending = False
            st.session_state.followup_text = ""
            # phase/advance logic
            answered = len(st.session_state.transcript)
            avg = get_avg_score()
            basic_len, inter_len = phase_length_plan(avg)
            # basic -> intermediate
            if st.session_state.phase == "basic":
                if answered >= basic_len:
                    st.session_state.phase = "intermediate"
                    st.session_state.current_question = None
                    st.session_state.intro_played = False
                else:
                    st.session_state.current_question = None
            elif st.session_state.phase == "intermediate":
                if answered >= basic_len + inter_len:
                    st.session_state.phase = "advanced"
                    st.session_state.current_question = None
                    st.session_state.intro_played = False
                else:
                    st.session_state.current_question = None
            elif st.session_state.phase == "advanced":
                # decide stop vs extend
                if answered < MIN_QUESTIONS:
                    st.session_state.current_question = None
                else:
                    # if strong or weak -> target MIN_QUESTIONS, else allow MAX_QUESTIONS
                    if avg is not None and (avg >= 4.5 or avg <= 2.0):
                        if answered >= MIN_QUESTIONS:
                            st.session_state.phase = "done"
                            st.session_state.interview_complete = True
                            st.session_state.current_question = None
                        else:
                            st.session_state.current_question = None
                    else:
                        if answered >= MAX_QUESTIONS:
                            st.session_state.phase = "done"
                            st.session_state.interview_complete = True
                            st.session_state.current_question = None
                        else:
                            st.session_state.current_question = None
        st.rerun()

# Follow-up UI
if st.session_state.followup_pending:
    st.markdown("### 🔎 Follow-up question (brief)")
    st.write(st.session_state.followup_text)
    if st.session_state.audio_allowed:
        play_audio_now(st.session_state.followup_text)
    fu_key = f"followup_{len(st.session_state.transcript)}"
    fu_answer = st.text_area("Your brief follow-up answer:", key=fu_key, height=120)
    if st.button("Submit Follow-up", key=f"submit_followup_{fu_key}"):
        # attach followup answer
        if st.session_state.transcript:
            st.session_state.transcript[-1]["followup_answer"] = fu_answer
        st.session_state.followup_pending = False
        st.session_state.followup_text = ""
        # After follow-up, advance same logic as normal submit (we reuse progression)
        answered = len(st.session_state.transcript)
        avg = get_avg_score()
        basic_len, inter_len = phase_length_plan(avg)
        if st.session_state.phase == "basic":
            if answered >= basic_len:
                st.session_state.phase = "intermediate"
                st.session_state.current_question = None
                st.session_state.intro_played = False
            else:
                st.session_state.current_question = None
        elif st.session_state.phase == "intermediate":
            if answered >= basic_len + inter_len:
                st.session_state.phase = "advanced"
                st.session_state.current_question = None
                st.session_state.intro_played = False
            else:
                    st.session_state.current_question = None
        elif st.session_state.phase == "advanced":
            if answered < MIN_QUESTIONS:
                st.session_state.current_question = None
            else:
                avg = get_avg_score()
                if avg is not None and (avg >= 4.5 or avg <= 2.0):
                    if answered >= MIN_QUESTIONS:
                        st.session_state.phase = "done"
                        st.session_state.interview_complete = True
                        st.session_state.current_question = None
                    else:
                        st.session_state.current_question = None
                else:
                    if answered >= MAX_QUESTIONS:
                        st.session_state.phase = "done"
                        st.session_state.interview_complete = True
                        st.session_state.current_question = None
                    else:
                        st.session_state.current_question = None
        st.rerun()

# Interview complete: show recruiter-style feedback, charts, PDF download
if st.session_state.get("interview_complete"):
    outro_text = f"Thank you {st.session_state.candidate_name or 'candidate'}. That concludes the interview. I will now share a structured feedback summary."
    st.success(outro_text)
    if st.session_state.audio_allowed:
        play_audio_now(outro_text)

    transcript = st.session_state.transcript
    scores = [t["evaluation"].get("score",3) for t in transcript]
    overall = sum(scores)/len(scores) if scores else 0.0

    # skill map, behavioral metrics
    skill_map = {}
    clarity_vals = []
    confidence_vals = []
    problem_vals = []
    for t in transcript:
        sa = t.get("skill_area","General")
        skill_map.setdefault(sa, []).append(t.get("evaluation",{}).get("score",3))
        clarity_vals.append(t.get("evaluation",{}).get("clarity",3))
        confidence_vals.append(t.get("evaluation",{}).get("confidence",3))
        problem_vals.append(t.get("evaluation",{}).get("problem_solving",3))

    st.header("📊 Scorecard")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Overall score", f"{overall:.2f}/5")
    with col2:
        st.metric("Tab changes during interview", st.session_state.tab_change_count)

    chart_bytes = skill_bar_chart_bytes(skill_map)
    st.image(chart_bytes, use_column_width=True)

    # strengths/weaknesses
    strengths = [k for k,v in skill_map.items() if sum(v)/len(v) >= 4]
    weaknesses = [k for k,v in skill_map.items() if sum(v)/len(v) <= 2.5]
    st.subheader("💡 Strengths & Weaknesses")
    if strengths:
        st.success("Strengths: " + ", ".join(strengths))
    if weaknesses:
        st.error("Weaknesses: " + ", ".join(weaknesses))
    if not strengths and not weaknesses:
        st.info("Balanced performance across skill areas.")

    st.subheader("🧭 Communication & Problem Solving")
    st.write(f"Average clarity: {sum(clarity_vals)/len(clarity_vals):.2f}/5")
    st.write(f"Average perceived confidence: {sum(confidence_vals)/len(confidence_vals):.2f}/5")
    st.write(f"Average problem-solving rating: {sum(problem_vals)/len(problem_vals):.2f}/5")

    # consistency metric
    consistency_raw = compute_consistency(transcript)
    consistency_scale = consistency_raw  # 0-1
    st.write(f"Consistency across answers (0-1): {consistency_raw:.2f}")

    # timings table & per-question time
    st.subheader("⏱️ Time taken per question")
    if st.session_state.timings:
        for i, tsec in enumerate(st.session_state.timings, 1):
            st.write(f"Q{i}: {int(tsec)} sec")
    else:
        st.write("No timing info recorded.")

    # Detailed transcript and feedback (now revealed)
    st.subheader("📝 Detailed Transcript & Feedback")
    for i, t in enumerate(transcript, 1):
        st.markdown(f"**Q{i} ({t.get('skill_area','')})**: {t['question']}")
        st.markdown(f"- **Your answer:** {t.get('answer','')}")
        ev = t.get("evaluation", {})
        st.markdown(f"- **Score:** {ev.get('score','N/A')}/5")
        st.markdown(f"- **Feedback:** {ev.get('feedback','')}")
        if t.get("followup_answer"):
            st.markdown(f"- **Follow-up answer:** {t.get('followup_answer')}")
        # timing if available
        if i-1 < len(st.session_state.timings):
            st.markdown(f"- **Time taken:** {int(st.session_state.timings[i-1])} sec")
        st.markdown("---")

    # recommendations
    st.subheader("📝 Recommendations & Next Steps")
    recs = []
    if weaknesses:
        recs.append("Focus on: " + ", ".join(weaknesses))
    else:
        recs.append("Solid technical foundation. Consider practicing scale/performance scenarios.")
    recs.append("Practice PivotTables, Power Query and INDEX/MATCH on real datasets.")
    recs.append("When answering, explain your approach step-by-step to show problem-solving.")
    for r in recs:
        st.write("- " + r)

    # PDF download includes timings and tab change count and consistency
    pdf = generate_pdf_report(st.session_state.candidate_name, transcript, overall, st.session_state.tab_change_count, timings=st.session_state.timings, consistency=consistency_raw)
    st.download_button("⬇️ Download full interview report (PDF)", data=pdf, file_name=f"{st.session_state.candidate_name or 'candidate'}_interview_report.pdf", mime="application/pdf")

    if st.button("🔄 Start new interview"):
        # clear session keys
        keys = ["phase","transcript","asked_skills","current_question","intro_played","followup_pending","followup_text","followup_limit","interview_complete","tab_change_count","timings","question_start","audio_allowed"]
        for k in keys:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()
