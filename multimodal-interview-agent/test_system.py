#!/usr/bin/env python3
"""
Quick system test to verify all components are working
"""

import requests
import json
import time

def test_backend_health():
    """Test if backend is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend server is running")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend connection failed: {e}")
        return False

def test_frontend_access():
    """Test if frontend is accessible"""
    try:
        response = requests.get("http://localhost:8503", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend is accessible")
            return True
        else:
            print(f"❌ Frontend access failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend connection failed: {e}")
        return False

def test_api_endpoints():
    """Test key API endpoints"""
    try:
        # Test analytics endpoint
        response = requests.get("http://localhost:8000/analytics", timeout=10)
        if response.status_code == 200:
            print("✅ Analytics API working")
            analytics = response.json()
            print(f"   - Total candidates: {analytics.get('total_candidates', 0)}")
        else:
            print(f"❌ Analytics API failed: {response.status_code}")
        
        # Test candidate creation
        candidate_data = {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+1-555-0123",
            "interview_role": "Data Scientist"
        }
        
        response = requests.post("http://localhost:8000/create-candidate", 
                               json=candidate_data, timeout=10)
        if response.status_code == 200:
            print("✅ Candidate creation API working")
            result = response.json()
            print(f"   - Created candidate ID: {result.get('candidate_id', 'N/A')}")
            return result.get('candidate_id')
        else:
            print(f"❌ Candidate creation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return None

def main():
    print("🧪 AI Interview Agent - System Test")
    print("=" * 40)
    
    # Test backend
    backend_ok = test_backend_health()
    
    # Test frontend
    frontend_ok = test_frontend_access()
    
    # Test APIs
    candidate_id = None
    if backend_ok:
        candidate_id = test_api_endpoints()
    
    print("\n📊 Test Results:")
    print(f"Backend Server: {'✅ OK' if backend_ok else '❌ FAILED'}")
    print(f"Frontend App: {'✅ OK' if frontend_ok else '❌ FAILED'}")
    print(f"API Endpoints: {'✅ OK' if candidate_id else '❌ FAILED'}")
    
    if backend_ok and frontend_ok:
        print("\n🎉 System is ready!")
        print("📱 Access the app at: http://localhost:8503")
        print("📚 API docs at: http://localhost:8000/docs")
        
        print("\n🚀 Next Steps:")
        print("1. Update your .env file with MongoDB Atlas connection string")
        print("2. Add your OpenAI API key to .env")
        print("3. Run: python database/init_db.py")
        print("4. Start testing the interview flow!")
    else:
        print("\n❌ System has issues. Please check:")
        print("1. Both servers are running")
        print("2. No port conflicts")
        print("3. All dependencies are installed")

if __name__ == "__main__":
    main()