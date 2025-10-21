from pymongo import MongoClient
from gridfs import GridFS
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

class MongoDBManager:
    def __init__(self, connection_string: str = None, db_name: str = None):
        self.connection_string = connection_string or os.getenv("MONGODB_CONNECTION_STRING")
        self.db_name = db_name or os.getenv("MONGODB_DATABASE_NAME", "interview_agent")
        
        if not self.connection_string:
            raise ValueError("MongoDB connection string is required. Please set MONGODB_CONNECTION_STRING in your .env file.")
        
        try:
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.db_name]
            self.fs = GridFS(self.db)
            
            # Test connection
            self.client.admin.command('ping')
            print(f"✅ Connected to MongoDB Atlas: {self.db_name}")
            
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            raise ConnectionError(f"Failed to connect to MongoDB: {e}")
    

        
        # Collections
        self.candidates = self.db.candidates
        self.sessions = self.db.interview_sessions
        self.evaluations = self.db.evaluations
        self.proctoring_events = self.db.proctoring_events
        self.audio_transcripts = self.db.audio_transcripts
        self.questions_responses = self.db.questions_responses
        self.tab_violations = self.db.tab_violations
        
        # Create indexes for better performance
        self._create_indexes()
    
    def create_candidate_profile(self, candidate_data: Dict) -> str:
        """Create new candidate profile"""
        candidate_data['created_at'] = datetime.utcnow()
        result = self.candidates.insert_one(candidate_data)
        return str(result.inserted_id)
    
    def create_interview_session(self, session_data: Dict) -> str:
        """Create new interview session"""
        session_data['created_at'] = datetime.utcnow()
        session_data['status'] = 'active'
        result = self.sessions.insert_one(session_data)
        return str(result.inserted_id)
    
    def store_resume_text(self, candidate_id: str, resume_text: str, resume_file: bytes = None) -> Dict:
        """Store resume text and optionally the PDF file"""
        resume_data = {
            'candidate_id': candidate_id,
            'resume_text': resume_text,
            'extracted_at': datetime.utcnow()
        }
        
        # Store PDF file in GridFS if provided
        if resume_file:
            file_id = self.fs.put(resume_file, filename=f"resume_{candidate_id}.pdf")
            resume_data['file_id'] = file_id
        
        # Update candidate profile
        self.candidates.update_one(
            {'_id': ObjectId(candidate_id)},
            {'$set': {'resume_data': resume_data}}
        )
        
        return resume_data
    
    def store_audio_transcript(self, session_id: str, audio_data: Dict) -> str:
        """Store audio transcript and analysis"""
        transcript_data = {
            'session_id': session_id,
            'timestamp': datetime.utcnow(),
            'transcript': audio_data.get('transcript', ''),
            'confidence_score': audio_data.get('confidence_score', 0),
            'speech_analysis': audio_data.get('speech_analysis', {}),
            'question_context': audio_data.get('question_context', ''),
            'response_evaluation': audio_data.get('response_evaluation', {})
        }
        
        result = self.audio_transcripts.insert_one(transcript_data)
        return str(result.inserted_id)
    
    def log_proctoring_event(self, session_id: str, event_data: Dict) -> str:
        """Log proctoring event"""
        event_record = {
            'session_id': session_id,
            'timestamp': datetime.utcnow(),
            'event_type': event_data.get('event_type'),
            'severity': event_data.get('severity', 'low'),
            'details': event_data.get('details', {}),
            'frame_analysis': event_data.get('frame_analysis', {})
        }
        
        result = self.proctoring_events.insert_one(event_record)
        return str(result.inserted_id)
    
    def store_evaluation_scores(self, session_id: str, evaluation_data: Dict) -> str:
        """Store comprehensive evaluation scores"""
        evaluation_record = {
            'session_id': session_id,
            'timestamp': datetime.utcnow(),
            'overall_score': evaluation_data.get('overall_score'),
            'detailed_scores': evaluation_data.get('detailed_scores', {}),
            'strengths': evaluation_data.get('strengths', []),
            'improvements': evaluation_data.get('improvements', []),
            'recommendation': evaluation_data.get('recommendation'),
            'rationale': evaluation_data.get('rationale', ''),
            'llm_analysis': evaluation_data.get('llm_analysis', {})
        }
        
        result = self.evaluations.insert_one(evaluation_record)
        return str(result.inserted_id)
    
    def get_session_data(self, session_id: str) -> Optional[Dict]:
        """Retrieve complete session data for report generation"""
        try:
            # Get session info
            session = self.sessions.find_one({'_id': ObjectId(session_id)})
            if not session:
                return None
            
            # Get candidate info
            candidate = self.candidates.find_one({'_id': ObjectId(session['candidate_id'])})
            
            # Get transcripts
            transcripts = list(self.audio_transcripts.find({'session_id': session_id}))
            
            # Get proctoring events
            proctoring_events = list(self.proctoring_events.find({'session_id': session_id}))
            
            # Get evaluation
            evaluation = self.evaluations.find_one({'session_id': session_id})
            
            return {
                'session': session,
                'candidate': candidate,
                'transcripts': transcripts,
                'proctoring_events': proctoring_events,
                'evaluation': evaluation
            }
        
        except Exception as e:
            print(f"Error retrieving session data: {e}")
            return None
    
    def update_session_status(self, session_id: str, status: str, additional_data: Dict = None) -> bool:
        """Update session status and optionally add additional data"""
        try:
            update_data = {
                'status': status,
                'updated_at': datetime.utcnow()
            }
            
            if additional_data:
                update_data.update(additional_data)
            
            result = self.sessions.update_one(
                {'_id': ObjectId(session_id)},
                {'$set': update_data}
            )
            
            return result.modified_count > 0
        
        except Exception as e:
            print(f"Error updating session status: {e}")
            return False
    
    def get_candidate_history(self, candidate_id: str) -> List[Dict]:
        """Get interview history for a candidate"""
        try:
            sessions = list(self.sessions.find({'candidate_id': candidate_id}))
            
            for session in sessions:
                # Add evaluation data
                evaluation = self.evaluations.find_one({'session_id': str(session['_id'])})
                if evaluation:
                    session['evaluation'] = evaluation
            
            return sessions
        
        except Exception as e:
            print(f"Error retrieving candidate history: {e}")
            return []
    
    def store_pdf_report(self, session_id: str, pdf_data: bytes, filename: str) -> str:
        """Store generated PDF report in GridFS"""
        try:
            file_id = self.fs.put(
                pdf_data,
                filename=filename,
                session_id=session_id,
                content_type='application/pdf',
                upload_date=datetime.utcnow()
            )
            
            # Update session with report file ID
            self.sessions.update_one(
                {'_id': ObjectId(session_id)},
                {'$set': {'report_file_id': file_id}}
            )
            
            return str(file_id)
        
        except Exception as e:
            print(f"Error storing PDF report: {e}")
            return None
    
    def get_pdf_report(self, file_id: str) -> Optional[bytes]:
        """Retrieve PDF report from GridFS"""
        try:
            file_data = self.fs.get(ObjectId(file_id))
            return file_data.read()
        
        except Exception as e:
            print(f"Error retrieving PDF report: {e}")
            return None
    
    def get_analytics_data(self, date_range: Dict = None) -> Dict:
        """Get analytics data for dashboard"""
        try:
            pipeline = []
            
            if date_range:
                pipeline.append({
                    '$match': {
                        'created_at': {
                            '$gte': date_range.get('start_date'),
                            '$lte': date_range.get('end_date')
                        }
                    }
                })
            
            # Aggregate session statistics
            session_stats = list(self.sessions.aggregate(pipeline + [
                {
                    '$group': {
                        '_id': None,
                        'total_sessions': {'$sum': 1},
                        'completed_sessions': {
                            '$sum': {'$cond': [{'$eq': ['$status', 'completed']}, 1, 0]}
                        }
                    }
                }
            ]))
            
            # Aggregate evaluation statistics
            eval_stats = list(self.evaluations.aggregate([
                {
                    '$group': {
                        '_id': None,
                        'avg_overall_score': {'$avg': '$overall_score'},
                        'total_evaluations': {'$sum': 1}
                    }
                }
            ]))
            
            return {
                'session_statistics': session_stats[0] if session_stats else {},
                'evaluation_statistics': eval_stats[0] if eval_stats else {},
                'proctoring_events_count': self.proctoring_events.count_documents({})
            }
        
        except Exception as e:
            print(f"Error retrieving analytics data: {e}")
            return {}
    
    def _create_indexes(self):
        """Create database indexes for better performance"""
        try:
            # Session indexes
            self.sessions.create_index("candidate_id")
            self.sessions.create_index("created_at")
            self.sessions.create_index("status")
            
            # Proctoring events indexes
            self.proctoring_events.create_index("session_id")
            self.proctoring_events.create_index("timestamp")
            self.proctoring_events.create_index("event_type")
            
            # Audio transcripts indexes
            self.audio_transcripts.create_index("session_id")
            self.audio_transcripts.create_index("timestamp")
            
            # Questions responses indexes
            self.questions_responses.create_index("session_id")
            self.questions_responses.create_index("question_number")
            
            print("✅ Database indexes created successfully")
        except Exception as e:
            print(f"⚠️ Warning: Could not create indexes: {e}")
    
    def store_question_response(self, session_id: str, question_data: Dict) -> str:
        """Store interview question and response pair"""
        qr_data = {
            'session_id': session_id,
            'timestamp': datetime.utcnow(),
            'question_number': question_data.get('question_number'),
            'question_text': question_data.get('question'),
            'candidate_response': question_data.get('response', ''),
            'response_timestamp': question_data.get('response_timestamp'),
            'evaluation_scores': question_data.get('evaluation', {}),
            'speech_analysis': question_data.get('speech_analysis', {}),
            'ai_feedback': question_data.get('ai_feedback', '')
        }
        
        result = self.questions_responses.insert_one(qr_data)
        return str(result.inserted_id)
    
    def store_tab_violation(self, session_id: str, violation_data: Dict) -> str:
        """Store tab switching violation with warning details"""
        violation_record = {
            'session_id': session_id,
            'timestamp': datetime.utcnow(),
            'violation_type': violation_data.get('violation_type', 'tab_switch'),
            'warning_number': violation_data.get('warning_number'),
            'total_violations': violation_data.get('total_violations'),
            'severity': violation_data.get('severity', 'medium'),
            'details': violation_data.get('details', {}),
            'user_warned': violation_data.get('user_warned', True)
        }
        
        result = self.tab_violations.insert_one(violation_record)
        return str(result.inserted_id)
    
    def get_session_violations(self, session_id: str) -> List[Dict]:
        """Get all violations for a specific session"""
        try:
            violations = list(self.tab_violations.find({'session_id': session_id}))
            proctoring_events = list(self.proctoring_events.find({'session_id': session_id}))
            
            return {
                'tab_violations': violations,
                'proctoring_events': proctoring_events,
                'total_violations': len(violations) + len(proctoring_events)
            }
        except Exception as e:
            print(f"Error retrieving session violations: {e}")
            return {'tab_violations': [], 'proctoring_events': [], 'total_violations': 0}
    
    def get_complete_interview_data(self, session_id: str) -> Optional[Dict]:
        """Get complete interview data including all components"""
        try:
            # Get session info
            session = self.sessions.find_one({'_id': ObjectId(session_id)})
            if not session:
                return None
            
            # Get candidate info
            candidate = self.candidates.find_one({'_id': ObjectId(session['candidate_id'])})
            
            # Get questions and responses
            questions_responses = list(self.questions_responses.find(
                {'session_id': session_id}
            ).sort('question_number', 1))
            
            # Get transcripts
            transcripts = list(self.audio_transcripts.find({'session_id': session_id}))
            
            # Get violations
            violations = self.get_session_violations(session_id)
            
            # Get evaluation
            evaluation = self.evaluations.find_one({'session_id': session_id})
            
            return {
                'session': session,
                'candidate': candidate,
                'questions_responses': questions_responses,
                'transcripts': transcripts,
                'violations': violations,
                'evaluation': evaluation,
                'interview_complete': session.get('status') == 'completed'
            }
        
        except Exception as e:
            print(f"Error retrieving complete interview data: {e}")
            return None
    
    def update_session_with_final_evaluation(self, session_id: str, final_evaluation: Dict) -> bool:
        """Update session with final evaluation and mark as completed"""
        try:
            # Store final evaluation
            eval_id = self.store_evaluation_scores(session_id, final_evaluation)
            
            # Update session status
            update_data = {
                'status': 'completed',
                'completed_at': datetime.utcnow(),
                'final_evaluation_id': eval_id,
                'total_questions': final_evaluation.get('question_count', 0),
                'overall_score': final_evaluation.get('overall_score', 0)
            }
            
            result = self.sessions.update_one(
                {'_id': ObjectId(session_id)},
                {'$set': update_data}
            )
            
            return result.modified_count > 0
        
        except Exception as e:
            print(f"Error updating session with final evaluation: {e}")
            return False
    
    def get_candidate_interview_history(self, candidate_email: str) -> List[Dict]:
        """Get all interview sessions for a candidate by email"""
        try:
            candidate = self.candidates.find_one({'email': candidate_email})
            if not candidate:
                return []
            
            sessions = list(self.sessions.find(
                {'candidate_id': str(candidate['_id'])}
            ).sort('created_at', -1))
            
            # Add evaluation data to each session
            for session in sessions:
                evaluation = self.evaluations.find_one({'session_id': str(session['_id'])})
                if evaluation:
                    session['evaluation'] = evaluation
                
                # Add violation count
                violations = self.get_session_violations(str(session['_id']))
                session['violation_count'] = violations['total_violations']
            
            return sessions
        
        except Exception as e:
            print(f"Error retrieving candidate history: {e}")
            return []
    
    def get_interview_analytics(self, date_range: Dict = None) -> Dict:
        """Get comprehensive interview analytics"""
        try:
            pipeline = []
            
            if date_range:
                pipeline.append({
                    '$match': {
                        'created_at': {
                            '$gte': date_range.get('start_date'),
                            '$lte': date_range.get('end_date')
                        }
                    }
                })
            
            # Session statistics
            session_stats = list(self.sessions.aggregate(pipeline + [
                {
                    '$group': {
                        '_id': None,
                        'total_sessions': {'$sum': 1},
                        'completed_sessions': {
                            '$sum': {'$cond': [{'$eq': ['$status', 'completed']}, 1, 0]}
                        },
                        'avg_score': {'$avg': '$overall_score'}
                    }
                }
            ]))
            
            # Role-wise statistics
            role_stats = list(self.sessions.aggregate(pipeline + [
                {
                    '$group': {
                        '_id': '$interview_role',
                        'count': {'$sum': 1},
                        'avg_score': {'$avg': '$overall_score'}
                    }
                }
            ]))
            
            # Violation statistics
            violation_stats = list(self.tab_violations.aggregate([
                {
                    '$group': {
                        '_id': '$violation_type',
                        'count': {'$sum': 1}
                    }
                }
            ]))
            
            return {
                'session_statistics': session_stats[0] if session_stats else {},
                'role_statistics': role_stats,
                'violation_statistics': violation_stats,
                'total_candidates': self.candidates.count_documents({}),
                'total_violations': self.tab_violations.count_documents({}) + 
                                  self.proctoring_events.count_documents({})
            }
        
        except Exception as e:
            print(f"Error retrieving analytics: {e}")
            return {}
    
    def cleanup_incomplete_sessions(self, hours_old: int = 24):
        """Clean up incomplete sessions older than specified hours"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours_old)
            
            result = self.sessions.delete_many({
                'status': {'$ne': 'completed'},
                'created_at': {'$lt': cutoff_time}
            })
            
            print(f"Cleaned up {result.deleted_count} incomplete sessions")
            return result.deleted_count
        
        except Exception as e:
            print(f"Error cleaning up sessions: {e}")
            return 0
    
    def close_connection(self):
        """Close MongoDB connection"""
        try:
            self.client.close()
            print("✅ MongoDB connection closed")
        except Exception as e:
            print(f"Error closing connection: {e}")