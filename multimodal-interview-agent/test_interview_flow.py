#!/usr/bin/env python3
"""
Test the complete interview flow
"""

import requests
import json
import base64

BACKEND_URL = "http://localhost:8000"

def test_complete_interview_flow():
    """Test the complete interview flow"""
    print("🧪 Testing Complete Interview Flow")
    print("=" * 40)
    
    try:
        # Step 1: Create candidate
        print("1. Creating candidate profile...")
        candidate_data = {
            "name": "Test Candidate",
            "email": "test@example.com",
            "phone": "+1-555-0123",
            "interview_role": "Data Scientist"
        }
        
        response = requests.post(f"{BACKEND_URL}/create-candidate", json=candidate_data)
        if response.status_code != 200:
            print(f"❌ Failed to create candidate: {response.text}")
            return False
        
        candidate_id = response.json()["candidate_id"]
        print(f"✅ Created candidate: {candidate_id}")
        
        # Step 2: Upload resume (simulate)
        print("2. Uploading resume...")
        resume_text = "Sample resume content for testing"
        files = {"file": ("resume.pdf", resume_text.encode(), "application/pdf")}
        data = {"candidate_id": candidate_id}
        
        response = requests.post(f"{BACKEND_URL}/upload-resume", files=files, data=data)
        if response.status_code != 200:
            print(f"❌ Failed to upload resume: {response.text}")
            return False
        
        print("✅ Resume uploaded successfully")
        
        # Step 3: Start interview session
        print("3. Starting interview session...")
        session_data = {
            "candidate_id": candidate_id,
            "interview_role": "Data Scientist",
            "candidate_background": "5 years experience in machine learning"
        }
        
        response = requests.post(f"{BACKEND_URL}/start-interview", json=session_data)
        if response.status_code != 200:
            print(f"❌ Failed to start interview: {response.text}")
            return False
        
        session_result = response.json()
        session_id = session_result["session_id"]
        first_question = session_result["first_question"]
        
        print(f"✅ Interview started: {session_id}")
        print(f"📝 First question: {first_question[:100]}...")
        
        # Step 4: Simulate answering questions
        print("4. Simulating interview responses...")
        
        for i in range(3):  # Test 3 questions
            print(f"   Question {i+1}...")
            
            # Simulate candidate response
            test_response = f"This is a test response to question {i+1}. I have experience with machine learning and data science."
            audio_data = base64.b64encode(test_response.encode()).decode()
            
            response = requests.post(f"{BACKEND_URL}/process-audio", json={
                "session_id": session_id,
                "audio_data": audio_data,
                "question_number": i + 1
            })
            
            if response.status_code != 200:
                print(f"❌ Failed to process response {i+1}: {response.text}")
                return False
            
            result = response.json()
            print(f"   ✅ Response processed, transcript: {result.get('transcript', 'N/A')[:50]}...")
            
            if result.get("interview_complete"):
                print("   🎉 Interview completed!")
                break
            elif result.get("next_question"):
                print(f"   📝 Next question: {result['next_question'][:50]}...")
        
        # Step 5: Get session data
        print("5. Retrieving session data...")
        response = requests.get(f"{BACKEND_URL}/session/{session_id}")
        if response.status_code != 200:
            print(f"❌ Failed to get session data: {response.text}")
            return False
        
        session_data = response.json()
        print(f"✅ Session data retrieved: {len(session_data.get('questions_responses', []))} Q&A pairs")
        
        print("\n🎉 Complete interview flow test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_complete_interview_flow()
    if success:
        print("\n✅ All tests passed! The interview system is working correctly.")
        print("🚀 You can now use the web interface at http://localhost:8503")
    else:
        print("\n❌ Tests failed. Please check the error messages above.")