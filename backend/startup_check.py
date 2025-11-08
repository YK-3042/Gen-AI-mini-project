#!/usr/bin/env python3
"""
Automated startup verification script for Maintenance Query Agent
Tests critical endpoints to ensure the application is working correctly
"""

import requests
import time
import sys
import os

API_BASE = "http://localhost:8000"
MAX_RETRIES = 3
RETRY_DELAY = 2

def print_status(emoji, message):
    """Print formatted status message"""
    print(f"{emoji} {message}")

def test_health():
    """Test /health endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        data = response.json()
        
        print_status("✓", f"Status Code: {response.status_code}")
        print_status("ℹ️", f"Response: {data}")
        
        if response.status_code == 200 and data.get("ok"):
            print_status("✅", "Health check PASSED")
            
            if data.get("faiss") == "not_ready":
                print_status("⚠️", "FAISS index not ready (no documents uploaded yet - this is expected)")
            
            return True
        else:
            print_status("❌", "Health check FAILED")
            return False
    
    except Exception as e:
        print_status("❌", f"Health check ERROR: {e}")
        return False

def test_admin_login():
    """Test /admin/login endpoint"""
    print("\n" + "="*60)
    print("TEST 2: Admin Login")
    print("="*60)
    
    admin_user = os.environ.get("ADMIN_USER", "yksw2403")
    admin_pass = os.environ.get("ADMIN_PASS", "240305")
    
    print_status("ℹ️", f"Attempting login with username: {admin_user}")
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post(
                f"{API_BASE}/admin/login",
                json={"username": admin_user, "password": admin_pass},
                timeout=10
            )
            
            print_status("ℹ️", f"Attempt {attempt + 1}/{MAX_RETRIES}")
            print_status("ℹ️", f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print_status("ℹ️", f"Response keys: {list(data.keys())}")
                
                if "token" in data:
                    print_status("✅", "Admin login PASSED")
                    print_status("ℹ️", f"Username: {data.get('username')}")
                    
                    if data.get("must_change_password"):
                        print_status("⚠️", "Password change required on first login")
                    
                    return True, data.get("token")
                else:
                    print_status("❌", "Login succeeded but no token returned")
                    return False, None
            else:
                print_status("⚠️", f"Login failed with status {response.status_code}: {response.text}")
                
                if attempt < MAX_RETRIES - 1:
                    print_status("ℹ️", f"Retrying in {RETRY_DELAY} seconds...")
                    time.sleep(RETRY_DELAY)
        
        except Exception as e:
            print_status("❌", f"Login ERROR on attempt {attempt + 1}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
    
    print_status("❌", "Admin login FAILED after all retries")
    print_status("💡", "Debug: Check if admin user exists in database")
    print_status("💡", f"Debug: Username '{admin_user}', ensure ADMIN_PASS is set correctly")
    
    return False, None

def test_chat():
    """Test /chat endpoint"""
    print("\n" + "="*60)
    print("TEST 3: Chat Endpoint")
    print("="*60)
    
    test_query = "What is a recommended lubrication interval for conveyor belts?"
    print_status("ℹ️", f"Test query: {test_query}")
    
    try:
        response = requests.post(
            f"{API_BASE}/chat",
            json={"query": test_query},
            timeout=30
        )
        
        print_status("ℹ️", f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print_status("ℹ️", f"Response keys: {list(data.keys())}")
            
            if "answer" in data:
                answer_preview = data["answer"][:150] + "..." if len(data["answer"]) > 150 else data["answer"]
                print_status("✅", "Chat endpoint PASSED")
                print_status("ℹ️", f"Answer preview: {answer_preview}")
                print_status("ℹ️", f"Used documents: {data.get('used_documents', False)}")
                print_status("ℹ️", f"Sources: {len(data.get('sources', []))}")
                
                if not data.get("used_documents"):
                    print_status("⚠️", "No documents uploaded yet - using general knowledge")
                
                return True
            else:
                print_status("❌", "Chat succeeded but no answer field")
                return False
        else:
            print_status("❌", f"Chat failed with status {response.status_code}: {response.text}")
            return False
    
    except Exception as e:
        print_status("❌", f"Chat ERROR: {e}")
        return False

def wait_for_server(max_wait=30):
    """Wait for server to be ready"""
    print_status("⏳", "Waiting for server to start...")
    
    for i in range(max_wait):
        try:
            response = requests.get(f"{API_BASE}/health", timeout=2)
            if response.status_code == 200:
                print_status("✓", "Server is ready!")
                return True
        except:
            pass
        
        time.sleep(1)
        if (i + 1) % 5 == 0:
            print_status("⏳", f"Still waiting... ({i + 1}s)")
    
    return False

def main():
    """Run all startup checks"""
    print("\n" + "="*60)
    print("🚀 MAINTENANCE QUERY AGENT - STARTUP VERIFICATION")
    print("="*60)
    
    if not wait_for_server():
        print_status("❌", "Server failed to start within timeout period")
        print_status("💡", "Ensure backend is running: cd backend && uvicorn main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    test_results = []
    
    health_ok = test_health()
    test_results.append(("Health Check", health_ok))
    
    login_ok, token = test_admin_login()
    test_results.append(("Admin Login", login_ok))
    
    chat_ok = test_chat()
    test_results.append(("Chat Endpoint", chat_ok))
    
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    all_passed = all(result for _, result in test_results)
    
    print("\n" + "="*60)
    
    if all_passed:
        print_status("🎉", "All startup checks PASSED - project generated and verified!")
        print("\n" + "="*60)
        print("NEXT STEPS:")
        print("="*60)
        
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            print_status("⚠️", "GEMINI_API_KEY not set - add it in Replit Secrets")
            print_status("💡", "Get your key from: https://aistudio.google.com/app/apikey")
        else:
            print_status("✅", "GEMINI_API_KEY is configured")
        
        print_status("🔐", "Default admin credentials: yksw2403 / 240305")
        print_status("⚠️", "Change password immediately via /admin panel")
        print_status("📚", "Upload maintenance documents via /admin to enable document-based Q&A")
        print_status("🌐", "Access the frontend in your browser")
        
        print("\n" + "="*60)
        sys.exit(0)
    else:
        print_status("❌", "Some startup checks FAILED")
        print("\n" + "="*60)
        print("TROUBLESHOOTING:")
        print("="*60)
        print_status("💡", "1. Check backend logs for errors")
        print_status("💡", "2. Verify GEMINI_API_KEY in Replit Secrets (if chat fails)")
        print_status("💡", "3. Ensure database initialized properly")
        print_status("💡", "4. Try setting custom ADMIN_USER/ADMIN_PASS in Replit Secrets")
        
        print("\n" + "="*60)
        sys.exit(1)

if __name__ == "__main__":
    main()
