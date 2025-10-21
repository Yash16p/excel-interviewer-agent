#!/usr/bin/env python3
"""
Database initialization script for MongoDB Atlas
Run this script to set up your database collections and indexes
"""

import os
import sys
from dotenv import load_dotenv

# Add parent directory to path to import mongo_utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.mongo_utils import MongoDBManager

def initialize_database():
    """Initialize MongoDB Atlas database with collections and sample data"""
    
    print("🚀 Initializing MongoDB Atlas Database...")
    
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize database manager
        db_manager = MongoDBManager()
        
        print("✅ Connected to MongoDB Atlas successfully!")
        
        # Test collections access
        collections = [
            'candidates',
            'interview_sessions', 
            'evaluations',
            'proctoring_events',
            'audio_transcripts',
            'questions_responses',
            'tab_violations'
        ]
        
        print("\n📋 Checking collections...")
        for collection_name in collections:
            collection = getattr(db_manager, collection_name)
            count = collection.count_documents({})
            print(f"  ✅ {collection_name}: {count} documents")
        
        # Create sample data for testing (optional)
        create_sample = input("\n❓ Create sample test data? (y/n): ").lower().strip()
        
        if create_sample == 'y':
            create_sample_data(db_manager)
        
        print("\n🎉 Database initialization completed successfully!")
        print("\n📝 Next steps:")
        print("1. Update your .env file with your MongoDB Atlas connection string")
        print("2. Start the backend server: uvicorn backend.main:app --reload")
        print("3. Start the frontend: streamlit run frontend/app.py")
        
        # Test database operations
        print("\n🧪 Testing database operations...")
        test_database_operations(db_manager)
        
        db_manager.close_connection()
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your MongoDB Atlas connection string in .env")
        print("2. Ensure your IP is whitelisted in MongoDB Atlas")
        print("3. Verify your database user has proper permissions")
        return False
    
    return True

def create_sample_data(db_manager):
    """Create sample data for testing"""
    print("\n📝 Creating sample test data...")
    
    try:
        # Sample candidate
        sample_candidate = {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-0123",
            "interview_role": "Data Scientist"
        }
        
        candidate_id = db_manager.create_candidate_profile(sample_candidate)
        print(f"  ✅ Created sample candidate: {candidate_id}")
        
        # Sample session
        sample_session = {
            "candidate_id": candidate_id,
            "interview_role": "Data Scientist",
            "candidate_background": "5 years experience in machine learning",
            "status": "completed"
        }
        
        session_id = db_manager.create_interview_session(sample_session)
        print(f"  ✅ Created sample session: {session_id}")
        
        # Sample question-response
        sample_qr = {
            "question": "Tell me about your experience with machine learning?",
            "response": "I have 5 years of experience working with various ML algorithms...",
            "question_number": 1,
            "evaluation": {
                "technical_accuracy": 8,
                "communication_clarity": 7,
                "overall_quality": 8
            }
        }
        
        qr_id = db_manager.store_question_response(session_id, sample_qr)
        print(f"  ✅ Created sample Q&A: {qr_id}")
        
        # Sample evaluation
        sample_evaluation = {
            "overall_score": 8.2,
            "detailed_scores": {
                "technical_accuracy": 8.5,
                "communication_clarity": 7.8,
                "problem_solving": 8.3
            },
            "strengths": ["Strong technical knowledge", "Clear communication"],
            "improvements": ["Could provide more specific examples"],
            "recommendation": "Hire"
        }
        
        eval_id = db_manager.store_evaluation_scores(session_id, sample_evaluation)
        print(f"  ✅ Created sample evaluation: {eval_id}")
        
        print("✅ Sample data created successfully!")
        
    except Exception as e:
        print(f"❌ Failed to create sample data: {e}")

def test_database_operations(db_manager):
    """Test basic database operations"""
    try:
        # Test analytics
        analytics = db_manager.get_interview_analytics()
        print(f"  ✅ Analytics query successful: {analytics.get('total_candidates', 0)} candidates")
        
        # Test session retrieval
        sessions = list(db_manager.sessions.find().limit(1))
        if sessions:
            session_data = db_manager.get_complete_interview_data(str(sessions[0]['_id']))
            print(f"  ✅ Session data retrieval successful")
        
        print("✅ All database operations working correctly!")
        
    except Exception as e:
        print(f"⚠️ Some database operations failed: {e}")

def show_connection_help():
    """Show help for MongoDB Atlas connection"""
    print("\n📚 MongoDB Atlas Connection Help:")
    print("="*50)
    print("1. Go to https://cloud.mongodb.com/")
    print("2. Create a new cluster or use existing one")
    print("3. Go to Database Access and create a user")
    print("4. Go to Network Access and add your IP (or 0.0.0.0/0 for testing)")
    print("5. Get your connection string from 'Connect' button")
    print("6. Update your .env file:")
    print("   MONGODB_CONNECTION_STRING=mongodb+srv://username:password@cluster.mongodb.net/")
    print("   MONGODB_DATABASE_NAME=interview_agent")
    print("\n🔗 Connection string format:")
    print("mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>?retryWrites=true&w=majority")

if __name__ == "__main__":
    print("🤖 AI Interview Agent - Database Setup")
    print("="*40)
    
    # Check if .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found!")
        print("Please create a .env file with your MongoDB Atlas connection details.")
        show_connection_help()
        sys.exit(1)
    
    # Check if MongoDB connection string is set
    load_dotenv()
    connection_string = os.getenv('MONGODB_CONNECTION_STRING')
    
    if not connection_string or 'your_' in connection_string:
        print("❌ MongoDB connection string not configured!")
        print("Please update your .env file with your actual MongoDB Atlas connection string.")
        show_connection_help()
        sys.exit(1)
    
    # Initialize database
    success = initialize_database()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("Your AI Interview Agent database is ready to use!")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        show_connection_help()