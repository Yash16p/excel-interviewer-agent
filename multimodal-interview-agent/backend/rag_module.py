from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from typing import List, Dict
import json

class RAGModule:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.encoder = SentenceTransformer(model_name)
        self.knowledge_base = {}
        self.indices = {}
        self.documents = {}
    
    def initialize_domain_knowledge(self, role: str, documents: List[str]):
        """Initialize role-specific knowledge base"""
        # Encode documents
        embeddings = self.encoder.encode(documents)
        
        # Create FAISS index
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)  # Inner product for similarity
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        index.add(embeddings.astype('float32'))
        
        # Store in role-specific containers
        self.indices[role] = index
        self.documents[role] = documents
        self.knowledge_base[role] = {
            "embeddings": embeddings,
            "documents": documents,
            "index": index
        }
    
    def retrieve_relevant_context(self, query: str, role: str, top_k: int = 3) -> List[Dict]:
        """Retrieve most relevant documents for query"""
        if role not in self.indices:
            return []
        
        # Encode query
        query_embedding = self.encoder.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search for similar documents
        scores, indices = self.indices[role].search(query_embedding.astype('float32'), top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents[role]):
                results.append({
                    "document": self.documents[role][idx],
                    "similarity_score": float(score),
                    "index": int(idx)
                })
        
        return results
    
    def generate_contextual_questions(self, role: str, candidate_background: str, difficulty_level: str = "medium") -> List[str]:
        """Generate role-specific interview questions"""
        question_templates = {
            "Data Scientist": [
                "Explain the bias-variance tradeoff and how it affects model performance.",
                "How would you handle missing data in a time series forecasting problem?",
                "Describe your approach to feature selection for high-dimensional datasets.",
                "Walk me through how you would validate a machine learning model in production."
            ],
            "Software Engineer": [
                "Explain the difference between composition and inheritance in OOP.",
                "How would you design a scalable system for handling millions of requests?",
                "Describe your approach to debugging a performance issue in production.",
                "Walk me through how you would implement a caching strategy."
            ],
            "Business Analyst": [
                "How would you identify key performance indicators for a new product?",
                "Describe your process for gathering and documenting requirements.",
                "Explain how you would present technical findings to non-technical stakeholders.",
                "Walk me through your approach to process improvement analysis."
            ]
        }
        
        base_questions = question_templates.get(role, [])
        
        # Customize questions based on candidate background
        context_query = f"candidate background: {candidate_background}"
        relevant_docs = self.retrieve_relevant_context(context_query, role, top_k=2)
        
        # In production, use LLM to generate personalized questions
        return base_questions[:4]  # Return first 4 questions for now
    
    def enhance_evaluation_context(self, answer: str, role: str) -> Dict:
        """Provide context for answer evaluation"""
        relevant_context = self.retrieve_relevant_context(answer, role, top_k=2)
        
        return {
            "relevant_knowledge": relevant_context,
            "role_expectations": self._get_role_expectations(role),
            "evaluation_criteria": self._get_evaluation_criteria(role)
        }
    
    def _get_role_expectations(self, role: str) -> Dict:
        """Get role-specific expectations"""
        expectations = {
            "Data Scientist": {
                "technical_depth": "Strong statistical and ML knowledge",
                "tools_familiarity": "Python, R, SQL, ML frameworks",
                "business_acumen": "Ability to translate business problems to ML solutions"
            },
            "Software Engineer": {
                "technical_depth": "Strong programming and system design skills",
                "tools_familiarity": "Programming languages, frameworks, databases",
                "problem_solving": "Algorithmic thinking and optimization"
            },
            "Business Analyst": {
                "analytical_skills": "Data analysis and process improvement",
                "communication": "Stakeholder management and documentation",
                "business_knowledge": "Understanding of business processes"
            }
        }
        return expectations.get(role, {})
    
    def _get_evaluation_criteria(self, role: str) -> List[str]:
        """Get role-specific evaluation criteria"""
        criteria = {
            "Data Scientist": [
                "Statistical knowledge accuracy",
                "ML algorithm understanding",
                "Data preprocessing skills",
                "Model evaluation techniques",
                "Business problem framing"
            ],
            "Software Engineer": [
                "Code quality and best practices",
                "System design thinking",
                "Algorithm complexity understanding",
                "Debugging and testing approach",
                "Scalability considerations"
            ],
            "Business Analyst": [
                "Requirements gathering process",
                "Data analysis methodology",
                "Stakeholder communication",
                "Process improvement approach",
                "Documentation quality"
            ]
        }
        return criteria.get(role, [])