import streamlit as st

# Configure Streamlit page - MUST be first Streamlit command
st.set_page_config(
    page_title="AI Interview Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

import requests
import base64
import json
from datetime import datetime
import time

from components.webcam import WebcamComponent
from components.audio import AudioComponent
from components.tab_monitor import TabMonitor

# Backend API URL
BACKEND_URL = "http://localhost:8000"

def initialize_session_state():
    """Initialize session state variables"""
    if 'interview_started' not in st.session_state:
        st.session_state.interview_started = False
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    if 'candidate_id' not in st.session_state:
        st.session_state.candidate_id = None
    if 'current_question' not in st.session_state:
        st.session_state.current_question = ""
    if 'question_number' not in st.session_state:
        st.session_state.question_number = 1
    if 'interview_complete' not in st.session_state:
        st.session_state.interview_complete = False
    if 'tab_monitor' not in st.session_state:
        st.session_state.tab_monitor = None

def create_candidate_profile(name, email, phone, role):
    """Create candidate profile via API"""
    try:
        response = requests.post(f"{BACKEND_URL}/create-candidate", json={
            "name": name,
            "email": email,
            "phone": phone,
            "interview_role": role
        })
        if response.status_code == 200:
            return response.json()["candidate_id"]
        else:
            st.error(f"Failed to create candidate profile: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error creating candidate profile: {e}")
        return None

def upload_resume(file, candidate_id):
    """Upload and process resume"""
    try:
        files = {"file": file}
        data = {"candidate_id": candidate_id}
        response = requests.post(f"{BACKEND_URL}/upload-resume", files=files, data=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to upload resume: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error uploading resume: {e}")
        return None

def start_interview_session(candidate_id, role, background):
    """Start interview session and get first question"""
    try:
        response = requests.post(f"{BACKEND_URL}/start-interview", json={
            "candidate_id": candidate_id,
            "interview_role": role,
            "candidate_background": background
        })
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to start interview: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error starting interview: {e}")
        return None

def process_audio_response(session_id, audio_data, question_number):
    """Process audio response and get next question"""
    try:
        # Convert audio to base64
        audio_b64 = base64.b64encode(audio_data).decode()
        
        response = requests.post(f"{BACKEND_URL}/process-audio", json={
            "session_id": session_id,
            "audio_data": audio_b64,
            "question_number": question_number
        })
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to process audio: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error processing audio: {e}")
        return None

def main():
    st.title("🤖 AI Interview Simulation Agent")
    
    # Check if running in demo mode
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=2)
        if response.status_code == 200:
            # Check if backend is in demo mode by testing database
            test_response = requests.get(f"{BACKEND_URL}/analytics", timeout=2)
            if test_response.status_code == 200:
                analytics = test_response.json()
                if analytics.get('total_candidates') == 0:
                    st.info("📝 **Demo Mode**: Running without database. Data will be stored temporarily in memory. For production use, configure MongoDB Atlas in your .env file.")
    except:
        pass
    
    st.markdown("---")
    
    initialize_session_state()
    
    # Sidebar for interview progress
    with st.sidebar:
        st.header("📊 Interview Progress")
        if st.session_state.interview_started:
            st.success("✅ Interview Active")
            st.info(f"Question: {st.session_state.question_number}/7")
            
            # Initialize tab monitor if not already done
            if st.session_state.tab_monitor is None:
                st.session_state.tab_monitor = TabMonitor(
                    session_id=st.session_state.session_id,
                    backend_url=BACKEND_URL
                )
            
            # Show proctoring rules
            st.session_state.tab_monitor.show_proctoring_rules()
        else:
            st.info("🔄 Ready to start")
    
    # Main interview interface
    if not st.session_state.interview_started:
        # Candidate onboarding phase
        st.header("👤 Candidate Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            candidate_name = st.text_input("Full Name *", placeholder="Enter your full name")
            candidate_email = st.text_input("Email Address *", placeholder="your.email@example.com")
            candidate_phone = st.text_input("Phone Number", placeholder="+1 (555) 123-4567")
        
        with col2:
            interview_role = st.selectbox("Interview Role *", 
                                        ["Data Scientist", "Software Engineer", "Business Analyst"])
            
            uploaded_resume = st.file_uploader("Upload Resume (PDF) *", type="pdf")
            
            candidate_background = st.text_area("Brief Background", 
                                               placeholder="Tell us about your experience and background...")
        
        st.markdown("---")
        
        # Validation and start button
        if candidate_name and candidate_email and uploaded_resume and interview_role:
            st.success("✅ All required information provided")
            
            if st.button("🚀 Start AI Interview", type="primary", use_container_width=True):
                with st.spinner("Setting up your interview..."):
                    # Create candidate profile
                    candidate_id = create_candidate_profile(
                        candidate_name, candidate_email, candidate_phone, interview_role
                    )
                    
                    if candidate_id:
                        st.session_state.candidate_id = candidate_id
                        
                        # Upload resume
                        resume_result = upload_resume(uploaded_resume, candidate_id)
                        
                        if resume_result:
                            # Start interview session
                            session_result = start_interview_session(
                                candidate_id, interview_role, candidate_background or "No background provided"
                            )
                            
                            if session_result:
                                st.session_state.session_id = session_result["session_id"]
                                st.session_state.current_question = session_result["first_question"]
                                st.session_state.question_number = session_result["question_number"]
                                st.session_state.interview_started = True
                                st.rerun()
        else:
            st.warning("⚠️ Please fill in all required fields marked with *")
    
    else:
        # Interview in progress
        if not st.session_state.interview_complete:
            st.header("🎤 Interview in Progress")
            
            # Initialize tab monitoring
            if st.session_state.tab_monitor:
                st.session_state.tab_monitor.initialize_tab_monitoring()
            
            # Display current question
            st.subheader(f"Question {st.session_state.question_number}")
            st.info(f"🤖 **AI Interviewer:** {st.session_state.current_question}")
            
            # AI Question Section
            st.markdown("### 🤖 AI Interviewer")
            
            # Display question with audio playback option
            st.info(f"🤖 **Question {st.session_state.question_number}:** {st.session_state.current_question}")
            
            # Generate question audio
            col_audio, col_text = st.columns([1, 3])
            
            with col_audio:
                if st.button("🔊 Play Audio", type="secondary"):
                    with st.spinner("🎵 Generating AI voice..."):
                        try:
                            response = requests.post(f"{BACKEND_URL}/generate-question-audio", 
                                                   json={"question": st.session_state.current_question})
                            if response.status_code == 200:
                                audio_data = response.json().get("audio_data")
                                if audio_data:
                                    st.success("🎵 AI question audio ready!")
                                    # Note: In a full implementation, this would play the audio
                                    st.info("🔊 Audio would play here (TTS generated)")
                                else:
                                    st.info("🔊 Audio generation not available")
                            else:
                                st.info("🔊 Audio generation not available")
                        except:
                            st.info("🔊 Audio generation not available")
            
            with col_text:
                st.markdown("**Listen to the AI question above, then record your response below.**")
            
            st.markdown("---")
            
            # Candidate Response Section
            st.markdown("### 🎙️ Your Response")
            
            # Audio component
            audio_component = AudioComponent()
            
            # Single, clean interface
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Try Streamlit native audio input first
                audio_response = None
                try:
                    if hasattr(st, 'audio_input'):
                        audio_response = st.audio_input("🎤 Record your response:")
                        if audio_response:
                            st.success("✅ Audio recorded!")
                            st.audio(audio_response)
                except:
                    pass
                
                # If no audio input available, show text input
                if not audio_response:
                    st.info("💬 **Please provide your response:**")
                    audio_response = st.text_area(
                        "Type your detailed response:", 
                        placeholder="Provide a comprehensive answer to the interview question...",
                        height=100,
                        key=f"response_{st.session_state.question_number}"
                    )
            
            with col2:
                st.markdown("**💡 Tips:**")
                st.markdown("""
                🎯 Be specific  
                🗣️ Stay focused  
                ⏱️ 1-2 minutes  
                💼 Professional tone
                """)
            
            # Submit Response
            st.markdown("---")
            
            if st.button("📤 Submit Response", type="primary", use_container_width=True):
                if audio_response:
                    with st.spinner("🤖 AI is analyzing your response..."):
                        # Prepare response data
                        if isinstance(audio_response, str):
                            response_data = audio_response.encode()
                        else:
                            response_data = audio_response
                        
                        # Process the response
                        result = process_audio_response(
                            st.session_state.session_id,
                            response_data,
                            st.session_state.question_number
                        )
                        
                        if result:
                            # Show transcript
                            transcript = result.get("transcript", audio_response if isinstance(audio_response, str) else "Response processed")
                            
                            st.markdown("**📝 Your Response:**")
                            st.write(transcript)
                            
                            # Show AI Evaluation (out of 5 points)
                            if result.get("evaluation"):
                                eval_data = result["evaluation"]
                                
                                # Convert 10-point scale to 5-point scale
                                overall_score = eval_data.get("overall_quality", 7) / 2
                                technical_score = eval_data.get("technical_accuracy", 7) / 2
                                clarity_score = eval_data.get("communication_clarity", 7) / 2
                                
                                st.markdown("### 📊 AI Evaluation")
                                
                                col_a, col_b, col_c = st.columns(3)
                                with col_a:
                                    st.metric("Technical", f"{technical_score:.1f}/5", 
                                             delta=f"{'Excellent' if technical_score >= 4 else 'Good' if technical_score >= 3 else 'Fair'}")
                                with col_b:
                                    st.metric("Clarity", f"{clarity_score:.1f}/5",
                                             delta=f"{'Excellent' if clarity_score >= 4 else 'Good' if clarity_score >= 3 else 'Fair'}")
                                with col_c:
                                    st.metric("Overall", f"{overall_score:.1f}/5",
                                             delta=f"{'Excellent' if overall_score >= 4 else 'Good' if overall_score >= 3 else 'Fair'}")
                                
                                # AI Feedback
                                st.markdown("**🤖 AI Feedback:**")
                                st.info(eval_data.get("feedback", "Good response! Keep up the great work."))
                            
                            # Check if interview is complete
                            if result.get("interview_complete"):
                                st.session_state.interview_complete = True
                                st.balloons()
                                st.success("🎉 Interview completed successfully!")
                                st.rerun()
                            else:
                                # Show next question and continue
                                if result.get("next_question"):
                                    st.session_state.current_question = result["next_question"]
                                    st.session_state.question_number = result.get("question_number", st.session_state.question_number + 1)
                                    
                                    st.success("✅ Response evaluated! Moving to next question...")
                                    time.sleep(2)
                                    st.rerun()
                        else:
                            st.error("❌ Failed to process response. Please try again.")
                else:
                    st.warning("⚠️ Please record your response or type your answer before submitting.")
            
            # Webcam monitoring
            st.markdown("### 📹 Video Monitoring")
            webcam_component = WebcamComponent()
            webcam_component.show_camera_placeholder()
            
        else:
            # Interview completed
            st.header("🎉 Interview Completed!")
            st.success("Thank you for completing the AI interview!")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.info("📊 **Interview Summary**")
                st.write(f"- Total Questions: {st.session_state.question_number}")
                st.write(f"- Session ID: {st.session_state.session_id}")
                st.write("- Status: Completed")
            
            with col2:
                st.info("📄 **Next Steps**")
                st.write("- Your responses have been recorded")
                st.write("- AI evaluation is being processed")
                st.write("- Report will be generated shortly")
            
            # Generate report button
            if st.button("📄 Generate Interview Report", type="primary"):
                with st.spinner("Generating your interview report..."):
                    try:
                        response = requests.get(f"{BACKEND_URL}/generate-report/{st.session_state.session_id}")
                        if response.status_code == 200:
                            st.success("✅ Report generated successfully!")
                            st.info("Your interview report has been saved and will be shared with the hiring team.")
                        else:
                            st.error("Failed to generate report. Please contact support.")
                    except Exception as e:
                        st.error(f"Error generating report: {e}")
            
            # Reset interview button
            if st.button("🔄 Start New Interview"):
                # Reset session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()

if __name__ == "__main__":
    main()