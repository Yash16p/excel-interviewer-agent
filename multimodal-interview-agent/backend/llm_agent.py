import openai
import os
from typing import Dict, List
import json
from dotenv import load_dotenv

load_dotenv()

class LLMAgent:
    def __init__(self, model="gpt-4o-mini"):
        self.model = model
        self.conversation_history = []
        self.evaluation_scores = {}
        self.question_count = 0
        self.max_questions = 7
        
        # Set up OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or "your_" in api_key:
            raise ValueError("OpenAI API key is required. Please set OPENAI_API_KEY in your .env file.")
        
        openai.api_key = api_key
        print("✅ OpenAI API key configured")
    
    def initialize_interview(self, role: str, candidate_background: str) -> str:
        """Initialize interview with role-specific context and generate first question"""
        self.role = role
        self.candidate_background = candidate_background
        self.conversation_history = []
        self.question_count = 0
        
        # Generate first question
        first_question = self._generate_opening_question(role, candidate_background)
        self.conversation_history.append({
            "type": "question",
            "content": first_question,
            "question_number": 1
        })
        self.question_count = 1
        
        return first_question
    
    def process_candidate_response(self, candidate_answer: str, speech_analysis: Dict = None) -> Dict:
        """Process candidate response and generate next question or conclude interview"""
        
        # Store candidate response
        self.conversation_history.append({
            "type": "answer",
            "content": candidate_answer,
            "question_number": self.question_count,
            "speech_analysis": speech_analysis or {}
        })
        
        # Evaluate current answer
        evaluation = self._evaluate_answer_with_ai(candidate_answer)
        
        # Check if interview should continue
        if self.question_count >= self.max_questions:
            return {
                "next_question": None,
                "evaluation": evaluation,
                "interview_complete": True,
                "final_evaluation": self.finalize_evaluation()
            }
        
        # Generate next question based on performance
        next_question = self._generate_dynamic_question(candidate_answer, evaluation)
        
        if next_question:
            self.question_count += 1
            self.conversation_history.append({
                "type": "question",
                "content": next_question,
                "question_number": self.question_count
            })
        
        return {
            "next_question": next_question,
            "evaluation": evaluation,
            "interview_complete": False,
            "question_number": self.question_count
        }
    
    def _generate_opening_question(self, role: str, candidate_background: str) -> str:
        """Generate role-specific opening question using AI"""
        
        role_contexts = {
            "Data Scientist": "machine learning, statistics, data analysis, Python, R, SQL, model deployment",
            "Software Engineer": "programming, system design, algorithms, data structures, software architecture",
            "Business Analyst": "business processes, requirements gathering, data analysis, stakeholder management"
        }
        
        context = role_contexts.get(role, "general technical skills")
        
        prompt = f"""
        You are an experienced interviewer conducting a {role} interview. 
        
        Candidate Background: {candidate_background}
        Role Context: {context}
        
        Generate an engaging opening question that:
        1. Is appropriate for a {role} position
        2. Allows the candidate to showcase their experience
        3. Is not too complex for the first question
        4. Relates to their background if relevant
        
        Return only the question, no additional text.
        """
        
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating opening question: {e}")
            return f"Tell me about your experience in {role.lower()} and what interests you most about this field."
    
    def _evaluate_answer_with_ai(self, answer: str) -> Dict:
        """Evaluate candidate's answer using AI"""
        
        conversation_context = "\n".join([
            f"{item['type'].title()}: {item['content']}" 
            for item in self.conversation_history[-4:]  # Last 2 Q&A pairs
        ])
        
        prompt = f"""
        You are a STRICT interviewer evaluating a {self.role} interview response. Be critical and accurate.
        
        Recent Conversation:
        {conversation_context}
        
        Current Answer: "{answer}"
        
        STRICT EVALUATION CRITERIA - Be harsh but fair:
        
        1. Technical accuracy/relevance (1-5):
           - 1: Wrong, irrelevant, or "I don't know"
           - 2: Partially correct but major gaps
           - 3: Generally correct with minor issues
           - 4: Accurate with good understanding
           - 5: Exceptional accuracy and insight
        
        2. Communication clarity (1-5):
           - 1: Unclear, confusing, or too brief
           - 2: Somewhat clear but lacks structure
           - 3: Clear and well-structured
           - 4: Very clear with good examples
           - 5: Exceptionally articulate
        
        3. Depth of knowledge (1-5):
           - 1: No depth, surface level only
           - 2: Basic understanding shown
           - 3: Good grasp of concepts
           - 4: Deep understanding with examples
           - 5: Expert-level knowledge
        
        4. Problem-solving approach (1-5):
           - 1: No clear approach or wrong method
           - 2: Basic approach with gaps
           - 3: Solid systematic approach
           - 4: Strong methodology with reasoning
           - 5: Excellent strategic thinking
        
        5. Overall quality (1-5):
           - 1: Poor response, inadequate
           - 2: Below average, needs improvement
           - 3: Average, meets basic expectations
           - 4: Good response, above average
           - 5: Excellent, impressive response
        
        SPECIAL CASES:
        - If answer is "I don't know" or similar: Give 1/5 for technical and depth
        - If answer is random text or very short: Give 1-2/5 across all areas
        - If answer is off-topic: Give 1/5 for technical accuracy
        
        Convert each 5-point score to 10-point scale by multiplying by 2.
        
        Return as JSON format:
        {{
            "technical_accuracy": score_out_of_10,
            "communication_clarity": score_out_of_10,
            "depth_of_knowledge": score_out_of_10,
            "problem_solving": score_out_of_10,
            "overall_quality": score_out_of_10,
            "feedback": "Score: X/5. [Specific feedback about the response quality]",
            "strengths": ["specific strength1", "specific strength2"],
            "improvements": ["specific improvement1", "specific improvement2"]
        }}
        """
        
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300,
                temperature=0.3
            )
            
            evaluation = json.loads(response.choices[0].message.content.strip())
            
            # Store scores for final evaluation
            for key, value in evaluation.items():
                if isinstance(value, (int, float)):
                    if key not in self.evaluation_scores:
                        self.evaluation_scores[key] = []
                    self.evaluation_scores[key].append(value)
            
            return evaluation
            
        except Exception as e:
            print(f"Error evaluating answer: {e}")
            return {
                "technical_accuracy": 7,
                "communication_clarity": 7,
                "depth_of_knowledge": 7,
                "problem_solving": 7,
                "overall_quality": 7,
                "feedback": "Unable to evaluate automatically. Manual review recommended.",
                "strengths": ["Provided a response"],
                "improvements": ["Could provide more detail"]
            }
    
    def _generate_dynamic_question(self, previous_answer: str, evaluation: Dict) -> str:
        """Generate next question based on candidate performance and conversation flow"""
        
        # Determine difficulty adjustment based on performance
        avg_score = sum([
            evaluation.get("technical_accuracy", 7),
            evaluation.get("communication_clarity", 7),
            evaluation.get("depth_of_knowledge", 7),
            evaluation.get("overall_quality", 7)
        ]) / 4
        
        if avg_score >= 8:
            difficulty = "increase difficulty and depth"
        elif avg_score >= 6:
            difficulty = "maintain current difficulty"
        else:
            difficulty = "simplify and provide more guidance"
        
        # Get conversation context
        conversation_context = "\n".join([
            f"{item['type'].title()}: {item['content']}" 
            for item in self.conversation_history[-6:]  # Last 3 Q&A pairs
        ])
        
        prompt = f"""
        You are conducting a {self.role} interview. This is question #{self.question_count + 1} of {self.max_questions}.
        
        Recent Conversation:
        {conversation_context}
        
        Latest Answer Evaluation:
        - Technical Accuracy: {evaluation.get('technical_accuracy', 7)}/10
        - Communication: {evaluation.get('communication_clarity', 7)}/10
        - Depth: {evaluation.get('depth_of_knowledge', 7)}/10
        - Overall: {evaluation.get('overall_quality', 7)}/10
        
        Performance Guidance: {difficulty}
        
        Generate the next question that:
        1. Builds naturally on the conversation
        2. Explores different aspects of {self.role} skills
        3. Adjusts difficulty based on performance
        4. Avoids repeating previous topics
        5. Is appropriate for question #{self.question_count + 1} of {self.max_questions}
        
        For the final questions (6-7), focus on scenario-based or advanced topics.
        
        Return only the question, no additional text.
        """
        
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.8
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error generating dynamic question: {e}")
            return "Can you tell me about a challenging project you've worked on and how you approached it?"
    
    def finalize_evaluation(self) -> Dict:
        """Generate comprehensive final evaluation using AI"""
        
        # Calculate average scores
        avg_scores = {}
        for key, scores in self.evaluation_scores.items():
            if isinstance(scores, list) and scores:
                avg_scores[key] = sum(scores) / len(scores)
        
        overall_score = sum(avg_scores.values()) / len(avg_scores) if avg_scores else 7.0
        
        # Generate comprehensive summary
        conversation_summary = "\n".join([
            f"Q{item.get('question_number', '')}: {item['content']}" 
            for item in self.conversation_history
        ])
        
        prompt = f"""
        Generate a comprehensive interview evaluation for a {self.role} candidate.
        
        Complete Interview Conversation:
        {conversation_summary}
        
        Average Scores:
        {json.dumps(avg_scores, indent=2)}
        
        Overall Score: {overall_score:.1f}/10
        
        Provide a detailed evaluation including:
        1. Overall assessment summary
        2. Top 3 strengths demonstrated
        3. Top 3 areas for improvement
        4. Hiring recommendation (Strong Hire/Hire/Weak Hire/No Hire)
        5. Rationale for recommendation
        
        Return as JSON:
        {{
            "overall_score": {overall_score:.1f},
            "detailed_scores": {json.dumps(avg_scores)},
            "summary": "comprehensive summary",
            "strengths": ["strength1", "strength2", "strength3"],
            "improvements": ["improvement1", "improvement2", "improvement3"],
            "recommendation": "hiring decision",
            "rationale": "detailed rationale"
        }}
        """
        
        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            final_eval = json.loads(response.choices[0].message.content.strip())
            final_eval["conversation_history"] = self.conversation_history
            final_eval["question_count"] = self.question_count
            
            return final_eval
            
        except Exception as e:
            print(f"Error generating final evaluation: {e}")
            return {
                "overall_score": overall_score,
                "detailed_scores": avg_scores,
                "summary": "Interview completed successfully with good engagement.",
                "strengths": ["Active participation", "Clear communication", "Technical knowledge"],
                "improvements": ["Could provide more specific examples", "Expand on technical details"],
                "recommendation": "Hire" if overall_score >= 7 else "Weak Hire",
                "rationale": f"Based on overall performance score of {overall_score:.1f}/10",
                "conversation_history": self.conversation_history,
                "question_count": self.question_count
            }