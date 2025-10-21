from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import PyPDF2
import io
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from parent directory
# Try .env.local first (for development), then .env
env_local_path = os.path.join(os.path.dirname(__file__), '..', '.env.local')
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')

if os.path.exists(env_local_path):
    load_dotenv(env_local_path)
    print("✅ Loaded development environment from .env.local")
else:
    load_dotenv(env_path)
    print("✅ Loaded environment from .env")

# Verify required environment variables are loaded
required_env_vars = ['MONGODB_CONNECTION_STRING', 'OPENAI_API_KEY']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]

if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}. Please check your .env file.")

from llm_agent import LLMAgent
from asr_module import ASRModule
from vision_module import VisionModule
from speech_analysis import SpeechAnalyzer
from rag_module import RAGModule
from pdf_report import PDFReportGenerator
from tts_module import TTSModule
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.mongo_utils import MongoDBManager

import uvicorn

app = FastAPI(title="Multimodal Interview Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize modules
db_manager = MongoDBManager()
asr_module = ASRModule()
vision_module = VisionModule()
speech_analyzer = SpeechAnalyzer()
rag_module = RAGModule()
pdf_generator = PDFReportGenerator()
tts_module = TTSModule()

# Pydantic models
class CandidateData(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    interview_role: str

class SessionStart(BaseModel):
    candidate_id: str
    interview_role: str
    candidate_background: str

class AudioProcessRequest(BaseModel):
    session_id: str
    audio_data: str  # base64 encoded
    question_number: int

class ProctorEventRequest(BaseModel):
    session_id: str
    event_type: str
    timestamp: str
    severity: str = "medium"
    details: Dict = {}

class TabViolationRequest(BaseModel):
    session_id: str
    violation_type: str = "tab_switch"
    warning_number: int
    total_violations: int
    details: Dict = {}

@app.post("/create-candidate")
async def create_candidate(candidate_data: CandidateData):
    """Create new candidate profile"""
    try:
        candidate_dict = candidate_data.dict()
        candidate_id = db_manager.create_candidate_profile(candidate_dict)
        return {"status": "success", "candidate_id": candidate_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create candidate: {str(e)}")

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...), candidate_id: str = ""):
    """Process uploaded resume and extract text"""
    try:
        # Read file content
        file_content = await file.read()
        resume_text = ""
        
        # Check if it's a PDF file or text file
        if file.content_type == "application/pdf" or file.filename.lower().endswith('.pdf'):
            try:
                # Extract text from PDF
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                for page in pdf_reader.pages:
                    resume_text += page.extract_text() + "\n"
            except Exception as pdf_error:
                # If PDF parsing fails, treat as text (for demo mode)
                print(f"PDF parsing failed, treating as text: {pdf_error}")
                resume_text = file_content.decode('utf-8', errors='ignore')
        else:
            # Treat as text file
            resume_text = file_content.decode('utf-8', errors='ignore')
        
        # If no text extracted, use filename as placeholder
        if not resume_text.strip():
            resume_text = f"Resume uploaded: {file.filename}\nContent extraction failed, but file was received successfully."
        
        # Store in database
        resume_data = db_manager.store_resume_text(candidate_id, resume_text, file_content)
        
        return {
            "status": "success", 
            "message": "Resume processed and stored",
            "resume_text": resume_text[:500] + "..." if len(resume_text) > 500 else resume_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process resume: {str(e)}")

@app.post("/start-interview")
async def start_interview(session_data: SessionStart):
    """Start new interview session and get first question"""
    try:
        # Create interview session
        session_dict = {
            "candidate_id": session_data.candidate_id,
            "interview_role": session_data.interview_role,
            "candidate_background": session_data.candidate_background,
            "status": "active"
        }
        session_id = db_manager.create_interview_session(session_dict)
        
        # Initialize LLM agent for this session
        llm_agent = LLMAgent()
        first_question = llm_agent.initialize_interview(
            session_data.interview_role, 
            session_data.candidate_background
        )
        
        # Store first question
        question_data = {
            "question": first_question,
            "question_number": 1,
            "timestamp": datetime.utcnow()
        }
        db_manager.store_question_response(session_id, question_data)
        
        # Generate TTS audio for the question
        question_audio = None
        try:
            question_audio = tts_module.speak_question(first_question, save_audio=False)
        except Exception as e:
            print(f"TTS generation failed: {e}")
        
        return {
            "status": "success",
            "session_id": session_id,
            "first_question": first_question,
            "question_number": 1,
            "question_audio": question_audio  # Base64 encoded audio or None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start interview: {str(e)}")

@app.post("/process-audio")
async def process_audio(request: AudioProcessRequest):
    """Convert audio to text and generate next question"""
    try:
        # Decode base64 audio data
        import base64
        audio_bytes = base64.b64decode(request.audio_data)
        
        # Check if this is text data (fallback when audio not available)
        try:
            # Try to decode as text first
            text_response = audio_bytes.decode('utf-8')
            if text_response and not text_response.startswith('simulated_audio') and len(text_response) > 10:
                # This is a text response
                transcript = text_response
                speech_analysis = {
                    "input_method": "text",
                    "fluency_score": 8.0,  # Default good score for text
                    "confidence_indicators": {"text_input": True},
                    "note": "Response provided via text input"
                }
            else:
                raise ValueError("Not a text response")
        except (UnicodeDecodeError, ValueError):
            # This is audio data, process normally
            if audio_bytes == b"simulated_audio_data" or audio_bytes == b"No response provided":
                # Handle simulated/empty responses
                transcript = "Thank you for your response. I understand you may be experiencing technical difficulties with audio recording."
                speech_analysis = {
                    "input_method": "simulated",
                    "fluency_score": 7.0,
                    "note": "Simulated response due to technical limitations"
                }
            else:
                # Real audio processing
                transcript = asr_module.transcribe(audio_bytes)
                
                # Speech analysis
                import numpy as np
                try:
                    audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
                    speech_analysis = speech_analyzer.analyze_speech_patterns(audio_array, transcript)
                except Exception as e:
                    print(f"Speech analysis error: {e}")
                    speech_analysis = {
                        "input_method": "audio",
                        "fluency_score": 7.0,
                        "note": "Speech analysis unavailable"
                    }
        
        # Get session data to continue conversation
        session_data = db_manager.get_complete_interview_data(request.session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Initialize LLM agent with session context
        llm_agent = LLMAgent()
        llm_agent.role = session_data['session']['interview_role']
        llm_agent.candidate_background = session_data['session']['candidate_background']
        
        # Restore conversation history
        for qr in session_data['questions_responses']:
            if qr['question_text']:
                llm_agent.conversation_history.append({
                    "type": "question",
                    "content": qr['question_text'],
                    "question_number": qr['question_number']
                })
            if qr['candidate_response']:
                llm_agent.conversation_history.append({
                    "type": "answer", 
                    "content": qr['candidate_response'],
                    "question_number": qr['question_number']
                })
        
        llm_agent.question_count = len([q for q in session_data['questions_responses'] if q['question_text']])
        
        # Process response and get next question
        response = llm_agent.process_candidate_response(transcript, speech_analysis)
        
        # Store question-response pair
        qr_data = {
            "question_number": request.question_number,
            "response": transcript,
            "response_timestamp": datetime.utcnow(),
            "evaluation": response.get("evaluation", {}),
            "speech_analysis": speech_analysis,
            "ai_feedback": response.get("evaluation", {}).get("feedback", "")
        }
        
        if response.get("next_question"):
            qr_data["question"] = response["next_question"]
            qr_data["question_number"] = response.get("question_number", request.question_number + 1)
        
        db_manager.store_question_response(request.session_id, qr_data)
        
        # If interview is complete, store final evaluation
        if response.get("interview_complete"):
            final_eval = response.get("final_evaluation", {})
            db_manager.update_session_with_final_evaluation(request.session_id, final_eval)
        
        return {
            "transcript": transcript,
            "next_question": response.get("next_question"),
            "evaluation": response.get("evaluation"),
            "interview_complete": response.get("interview_complete", False),
            "question_number": response.get("question_number"),
            "speech_analysis": speech_analysis
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process audio: {str(e)}")

@app.post("/log-proctoring-event")
async def log_proctoring_event(request: ProctorEventRequest):
    """Log proctoring event to database"""
    try:
        event_data = {
            "event_type": request.event_type,
            "severity": request.severity,
            "details": request.details
        }
        
        event_id = db_manager.log_proctoring_event(request.session_id, event_data)
        return {"status": "success", "event_id": event_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log event: {str(e)}")

@app.post("/log-tab-violation")
async def log_tab_violation(request: TabViolationRequest):
    """Log tab switching violation"""
    try:
        violation_data = {
            "violation_type": request.violation_type,
            "warning_number": request.warning_number,
            "total_violations": request.total_violations,
            "severity": "high" if request.total_violations > 3 else "medium",
            "details": request.details,
            "user_warned": True
        }
        
        violation_id = db_manager.store_tab_violation(request.session_id, violation_data)
        return {"status": "success", "violation_id": violation_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to log violation: {str(e)}")

@app.post("/analyze-video")
async def analyze_video(frame_data: bytes):
    """Analyze video frame for proctoring"""
    try:
        import numpy as np
        import cv2
        
        # Convert bytes to image
        nparr = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        analysis = vision_module.analyze_frame(frame)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze video: {str(e)}")

@app.get("/session/{session_id}")
async def get_session_data(session_id: str):
    """Get complete session data"""
    try:
        session_data = db_manager.get_complete_interview_data(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get session data: {str(e)}")

@app.get("/generate-report/{session_id}")
async def generate_report(session_id: str):
    """Generate final PDF report"""
    try:
        # Get complete session data
        session_data = db_manager.get_complete_interview_data(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Generate PDF report
        report_filename = pdf_generator.create_report(session_data)
        
        # Store PDF in database
        with open(report_filename, 'rb') as f:
            pdf_data = f.read()
        
        file_id = db_manager.store_pdf_report(session_id, pdf_data, report_filename)
        
        return {
            "status": "success",
            "report_filename": report_filename,
            "file_id": file_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")

@app.get("/analytics")
async def get_analytics():
    """Get interview analytics dashboard data"""
    try:
        analytics = db_manager.get_interview_analytics()
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@app.post("/generate-question-audio")
async def generate_question_audio(request: dict):
    """Generate TTS audio for a question"""
    try:
        question_text = request.get("question", "")
        if not question_text:
            raise HTTPException(status_code=400, detail="Question text is required")
        
        # Generate audio
        audio_data = tts_module.speak_question(question_text, save_audio=False)
        
        return {
            "status": "success",
            "audio_data": audio_data,  # Base64 encoded audio
            "message": "Question audio generated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate audio: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)