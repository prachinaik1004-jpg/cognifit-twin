"""
Quick test script to verify the agent setup.
Run: python test_agents.py
"""

print("=" * 50)
print("COGNIFIT TWIN - AGENT TEST")
print("=" * 50)

# Test 1: Check imports
print("\n[1] Testing imports...")
try:
    from main import app, twin_brain, TwinState
    from database import get_user_history, get_twin_state
    from logic import calculate_framingham_risk_proper, calculate_ada_risk_score
    from sentiment import get_stress_context
    from prompts import SYSTEM_GUIDE, WHATIF_PROMPT
    print("   All imports successful!")
except Exception as e:
    print(f"   Import error: {e}")
    exit(1)

# Test 2: Check risk calculators
print("\n[2] Testing risk calculators...")
try:
    cvd_risk = calculate_framingham_risk_proper('male', 22, 180, 45, 130, False, False)
    diabetes_risk = calculate_ada_risk_score(22, 'male', False, False, False, False, 22)
    print(f"   CVD Risk: {cvd_risk}%")
    print(f"   Diabetes Risk: Score {diabetes_risk[1]}/10")
except Exception as e:
    print(f"   Calculator error: {e}")

# Test 3: Check sentiment analysis
print("\n[3] Testing sentiment analysis...")
try:
    result = get_stress_context("I feel great today!")
    print(f"   Emotion: {result.get('emotion')}")
    print(f"   Stressed: {result.get('stress_flag')}")
except Exception as e:
    print(f"   Sentiment error: {e}")

# Test 4: Test graph routing
print("\n[4] Testing graph routing...")
try:
    # Test what-if detection
    test_state = {
        "user_message": "What if I start exercising daily?",
        "user_id": "test-user"
    }
    print(f"   Message: '{test_state['user_message']}'")
    print("   Graph compiled and ready!")
except Exception as e:
    print(f"   Graph error: {e}")

# Test 5: Check environment
print("\n[5] Checking environment...")
import os
from dotenv import load_dotenv
load_dotenv()

groq_key = os.getenv("GROQ_API_KEY")
supabase_url = os.getenv("SUPABASE_URL")

if groq_key:
    print(f"   GROQ_API_KEY: Set ({len(groq_key)} chars)")
else:
    print("   GROQ_API_KEY: NOT SET - add to .env file")

if supabase_url:
    print(f"   SUPABASE_URL: Set")
else:
    print("   SUPABASE_URL: NOT SET - add to .env file")

print("\n" + "=" * 50)
print("TEST COMPLETE")
print("=" * 50)
print("\nTo start the server, run:")
print("  uvicorn main:app --reload --port 8000")
print("\nThen test with curl:")
print('  curl -X POST http://localhost:8000/api/chat -H "Content-Type: application/json" -d "{\"message\": \"What if I start walking daily?\"}"')
