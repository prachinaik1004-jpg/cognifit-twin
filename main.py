import os
import json
from datetime import datetime
from typing import TypedDict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from groq import Groq
from dotenv import load_dotenv
from google_fit import get_auth_url, exchange_code_for_tokens, sync_all_data
from database import get_wearable_data, get_wearable_connection_status

# LangGraph imports
from langgraph.graph import StateGraph, END

# Import your other files
from sentiment import get_stress_context
from prompts import SYSTEM_GUIDE, WHATIF_PROMPT

# Import database and logic functions
from database import get_user_history, get_clinical_rag, get_twin_state, save_conversation_turn, create_user, log_daily_activity, get_conversation_history, save_manual_health_data
from logic import calculate_framingham_risk_proper, calculate_ada_risk_score

load_dotenv()
app = FastAPI()

# CORS configuration for Prachi
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# --- 1. LANGGRAPH STATE DEFINITION ---
class TwinState(TypedDict):
    user_message: str
    user_id: str
    emotion_data: dict
    simulation_result: dict
    ai_final_reply: str

# --- 2. THE AGENT NODES ---

def triage_agent(state: TwinState):
    """Agent 1: Checks the mood and stress levels."""
    print("--- [A2A] Agent 1: Triage analyzing message ---")
    stress_results = get_stress_context(state["user_message"])
    return {"emotion_data": stress_results}

def clinical_twin_agent(state: TwinState):
    """Agent 2: Reasons using Clinical Guidelines and User Bio."""
    print("--- [A2A] Agent 2: Twin generating response ---")
    
    user_id = state.get("user_id", "00000000-0000-0000-0000-000000000001")
    
    # Fetch REAL user data from database
    try:
        user_history = get_user_history(user_id)
        clinical_guidelines = get_clinical_rag(state["user_message"])
        user_state = get_twin_state(user_id)
    except Exception as e:
        print(f"Database fetch error: {e}")
        user_history = {"behavioral_facts": [], "recent_logs": []}
        clinical_guidelines = []
        user_state = {}
    
    # Build user context from real data
    user_context = f"Behavioral patterns: {user_history.get('behavioral_facts', [])}. Recent activity: {user_history.get('recent_logs', [])}"
    rag_chunks = str(clinical_guidelines) if clinical_guidelines else "No specific guidelines found."
    
    final_prompt = SYSTEM_GUIDE.format(
        user_context=user_context,
        rag_chunks=rag_chunks,
        stress_info=state["emotion_data"]
    )
    
    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": final_prompt},
            {"role": "user", "content": state["user_message"]}
        ],
        model="llama-3.3-70b-versatile",
    )
    
    # Log conversation to database
    try:
        save_conversation_turn(user_id, "user", state["user_message"], "chat")
        save_conversation_turn(user_id, "assistant", chat_completion.choices[0].message.content, "clinical_twin")
    except Exception as e:
        print(f"Conversation logging error: {e}")
    
    # Extract and log daily activities (meals, exercise, sleep, etc.)
    try:
        extract_prompt = f"""Extract any health-related activities from this user message. Return JSON with an "activities" array.

User message: {state["user_message"]}

Look for:
- Meals eaten (breakfast, lunch, dinner, snacks)
- Exercise or physical activity
- Sleep information
- Medication taken
- Water intake
- Stress or mood events

If no activities found, return: {{"activities": []}}
If found, return: {{"activities": [{{"type": "meal|exercise|sleep|medication|water|mood", "description": "brief description"}}]}}

Return ONLY valid JSON."""

        extract_response = client.chat.completions.create(
            messages=[{"role": "user", "content": extract_prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        extracted = json.loads(extract_response.choices[0].message.content)
        
        for activity in extracted.get("activities", []):
            log_type = activity.get("type", "general")
            description = activity.get("description", state["user_message"])
            log_entry = f"[{log_type}] {description}"
            metadata = {"type": log_type, "description": description}
            log_daily_activity(user_id, log_entry, log_type=log_type, metadata=metadata)
            print(f"--- Logged daily activity: {log_entry} ---")
    except Exception as e:
        print(f"Activity extraction error: {e}")
    
    # Extract health metrics from chat and save to wearable_data
    try:
        metrics_prompt = f"""Extract any quantifiable health metrics from this user message. Return JSON.

User message: {state["user_message"]}

Look for:
- Step count (e.g., "I walked 5000 steps", "5000 steps today")
- Heart rate (e.g., "my heart rate is 72", "resting heart rate 68")
- Sleep hours (e.g., "I slept 7 hours", "got 6.5 hours of sleep")
- Blood pressure (e.g., "blood pressure 120/80")

If no metrics found, return: {{"metrics": []}}
If found, return: {{"metrics": [{{"type": "steps|heart_rate|sleep|blood_pressure", "value": <number>, "unit": "steps|bpm|hours|mmHg"}}]}}

Return ONLY valid JSON."""

        metrics_response = client.chat.completions.create(
            messages=[{"role": "user", "content": metrics_prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        metrics_extracted = json.loads(metrics_response.choices[0].message.content)
        
        for metric in metrics_extracted.get("metrics", []):
            metric_type = metric.get("type")
            metric_value = metric.get("value")
            
            if metric_type and metric_value:
                # Map to wearable_data format
                if metric_type == "steps":
                    save_manual_health_data(user_id, "steps", {"steps": int(metric_value), "date": datetime.utcnow().strftime('%Y-%m-%d')})
                    print(f"--- Saved steps metric: {metric_value} ---")
                elif metric_type == "heart_rate":
                    save_manual_health_data(user_id, "heart_rate", {"bpm": int(metric_value), "date": datetime.utcnow().strftime('%Y-%m-%d')})
                    print(f"--- Saved heart rate metric: {metric_value} bpm ---")
                elif metric_type == "sleep":
                    save_manual_health_data(user_id, "sleep", {"hours": float(metric_value), "date": datetime.utcnow().strftime('%Y-%m-%d')})
                    print(f"--- Saved sleep metric: {metric_value} hours ---")
                elif metric_type == "blood_pressure":
                    save_manual_health_data(user_id, "blood_pressure", {"reading": str(metric_value), "date": datetime.utcnow().strftime('%Y-%m-%d')})
                    print(f"--- Saved blood pressure metric: {metric_value} ---")
    except Exception as e:
        print(f"Health metrics extraction error: {e}")
    
    # Check if user has wearable data - if not, append health questions
    try:
        from database import get_latest_wearable_data
        has_steps = get_latest_wearable_data(user_id, "steps") is not None
        has_hr = get_latest_wearable_data(user_id, "heart_rate") is not None
        has_sleep = get_latest_wearable_data(user_id, "sleep") is not None
        
        if not (has_steps and has_hr and has_sleep):
            missing = []
            if not has_steps:
                missing.append("your daily step count")
            if not has_hr:
                missing.append("your resting heart rate")
            if not has_sleep:
                missing.append("your average sleep hours")
            
            question = f"\n\n💡 By the way, I don't have data for {' and '.join(missing)} yet. Could you share that? For example: \"I walked about 5000 steps today\" or \"My resting heart rate is around 72\". This helps me give you better personalized insights!"
            chat_completion_content = chat_completion.choices[0].message.content + question
        else:
            chat_completion_content = chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Wearable data check error: {e}")
        chat_completion_content = chat_completion.choices[0].message.content
    
    return {"ai_final_reply": chat_completion_content}

def emergency_alert_agent(state: TwinState):
    """Agent 4: Handles critical safety warnings."""
    print("--- [A2A] Agent 4: Emergency Alert Triggered! ---")
    emergency_msg = (
        "⚠️ EMERGENCY DETECTED: Your symptoms or stress levels suggest a critical risk. "
        "Please stop what you are doing, prioritize rest, and seek medical attention if pain persists. "
        "I have flagged this for your clinical record."
    )
    return {"ai_final_reply": emergency_msg}

def whatif_simulator_agent(state: TwinState):
    """Agent 3: Simulates hypothetical health scenarios using real user data."""
    print("--- [A2A] Agent 3: What-If Simulator ---")
    
    user_id = state.get("user_id", "00000000-0000-0000-0000-000000000001")
    user_msg = state["user_message"]
    emotion_data = state["emotion_data"]
    
    # Fetch REAL user data
    try:
        user_history = get_user_history(user_id)
        user_state = get_twin_state(user_id)
        clinical_context = get_clinical_rag(user_msg)
    except Exception as e:
        print(f"Database fetch error: {e}")
        user_history = {"behavioral_facts": [], "recent_logs": []}
        user_state = {}
        clinical_context = []
    
    # Default user profile (can be overridden by database values)
    user_profile = {
        "age": user_state.get("age", 22),
        "gender": user_state.get("gender", "male"),
        "total_chol": user_state.get("total_chol", 180),
        "hdl": user_state.get("hdl", 45),
        "sbp": user_state.get("sbp", 130),
        "is_treated": user_state.get("on_bp_meds", False),
        "smoker": user_state.get("smoker", False),
        "bmi": user_state.get("bmi", 22),
        "active": user_state.get("physically_active", False),
        "family_hx_diabetes": user_state.get("family_hx_diabetes", False),
        "hypertension": user_state.get("hypertension", False),
    }
    
    # Calculate CURRENT risks using real data
    current_cvd = calculate_framingham_risk_proper(
        user_profile["gender"],
        user_profile["age"],
        user_profile["total_chol"],
        user_profile["hdl"],
        user_profile["sbp"],
        user_profile["is_treated"],
        user_profile["smoker"]
    )
    
    current_diabetes = calculate_ada_risk_score(
        user_profile["age"],
        user_profile["gender"],
        False,
        user_profile["family_hx_diabetes"],
        user_profile["hypertension"],
        user_profile["active"],
        user_profile["bmi"]
    )
    
    # Extract scenario from user message using LLM
    scenario_prompt = f"""Extract the health scenario from this message and return JSON with modifications.
    
Message: {user_msg}

Possible modifications:
- "smoker": true/false
- "active": true/false (physically active)
- "bmi": number (BMI value)
- "sbp": number (systolic blood pressure)

Return ONLY valid JSON like: {{"modifications": {{"active": true, "bmi": 20}}, "description": "daily exercise"}}
"""
    
    try:
        scenario_response = client.chat.completions.create(
            messages=[{"role": "user", "content": scenario_prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        scenario = json.loads(scenario_response.choices[0].message.content)
    except Exception as e:
        print(f"Scenario extraction error: {e}")
        scenario = {"modifications": {}, "description": "unknown change"}
    
    # Simulate with modified params
    simulated_profile = user_profile.copy()
    simulated_profile.update(scenario.get("modifications", {}))
    
    simulated_cvd = calculate_framingham_risk_proper(
        simulated_profile["gender"],
        simulated_profile["age"],
        simulated_profile["total_chol"],
        simulated_profile["hdl"],
        simulated_profile["sbp"],
        simulated_profile["is_treated"],
        simulated_profile["smoker"]
    )
    
    simulated_diabetes = calculate_ada_risk_score(
        simulated_profile["age"],
        simulated_profile["gender"],
        False,
        simulated_profile["family_hx_diabetes"],
        simulated_profile["hypertension"],
        simulated_profile["active"],
        simulated_profile["bmi"]
    )
    
    # Generate personalized response
    final_prompt = WHATIF_PROMPT.format(
        user_profile=user_profile,
        behavioral_facts=user_history.get('behavioral_facts', []),
        recent_logs=user_history.get('recent_logs', []),
        emotion_data=emotion_data,
        current_cvd=current_cvd,
        current_diabetes=current_diabetes[1],
        scenario=scenario.get('description', 'this change'),
        simulated_cvd=simulated_cvd,
        simulated_diabetes=simulated_diabetes[1],
        clinical_context=clinical_context
    )
    
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": final_prompt}],
        model="llama-3.3-70b-versatile"
    )
    
    # Log conversation
    try:
        save_conversation_turn(user_id, "user", user_msg, "chat")
        save_conversation_turn(user_id, "assistant", response.choices[0].message.content, "whatif_simulator")
    except Exception as e:
        print(f"Conversation logging error: {e}")
    
    return {
        "ai_final_reply": response.choices[0].message.content,
        "simulation_result": {
            "scenario": scenario,
            "before": {"cvd": current_cvd, "diabetes": current_diabetes[1]},
            "after": {"cvd": simulated_cvd, "diabetes": simulated_diabetes[1]}
        }
    }

# --- 3. CONDITIONAL ROUTING LOGIC ---

def route_request(state: TwinState):
    """Decider: Routes to appropriate agent based on intent."""
    print("--- [A2A] Routing Decision ---")
    data = state.get("emotion_data", {})
    msg_lower = state["user_message"].lower()
    
    # Priority 1: Emergency - high stress or pain keywords
    is_high_stress = data.get("stress_score", 0) > 0.8
    has_pain_keywords = any(word in msg_lower for word in ["pain", "hurt", "emergency", "dying", "racing"])
    
    if is_high_stress or has_pain_keywords:
        return "emergency"
    
    # Priority 2: What-If Simulation
    if "what if" in msg_lower:
        return "whatif_simulator"
    
    # Priority 3: Normal clinical query
    return "clinical_twin"

# --- 4. WIRING THE GRAPH ---

workflow = StateGraph(TwinState)

# Define Nodes
workflow.add_node("triage", triage_agent)
workflow.add_node("clinical_twin", clinical_twin_agent)
workflow.add_node("emergency_alert", emergency_alert_agent)
workflow.add_node("whatif_simulator", whatif_simulator_agent)

# Define Logic Flow
workflow.set_entry_point("triage")

workflow.add_conditional_edges(
    "triage",
    route_request,
    {
        "emergency": "emergency_alert",
        "whatif_simulator": "whatif_simulator",
        "clinical_twin": "clinical_twin"
    }
)

workflow.add_edge("emergency_alert", END)
workflow.add_edge("clinical_twin", END)
workflow.add_edge("whatif_simulator", END)

# Compile
twin_brain = workflow.compile()

# --- 5. FASTAPI ENDPOINTS ---

@app.get("/")
def home():
    return {"status": "Backend live with LangGraph & Autonomous Routing"}

@app.post("/api/chat")
async def chat(payload: dict):
    print("--- API REQUEST RECEIVED ---")
    try:
        user_msg = payload.get("message")
        user_id = payload.get("user_id", "00000000-0000-0000-0000-000000000001")
        initial_input = {"user_message": user_msg, "user_id": user_id}
        final_state = twin_brain.invoke(initial_input)
        
        response = {
            "reply": final_state["ai_final_reply"],
            "emotion": final_state["emotion_data"].get('emotion', 'neutral')
        }
        
        # Include simulation results if available
        if final_state.get("simulation_result"):
            response["simulation"] = final_state["simulation_result"]
        
        return response
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        return {"error": "Internal Server Error", "details": str(e)}

@app.post("/api/user/register")
async def register_user(payload: dict):
    """Register a new user with their health profile from onboarding."""
    print("--- USER REGISTRATION REQUEST ---")
    try:
        user_data = payload.get("user_data", {})
        result = create_user(user_data)
        return {"success": True, "user_id": result["user_id"], "user": result}
    except Exception as e:
        print(f"User registration error: {e}")
        return {"error": "Registration failed", "details": str(e)}

@app.get("/api/user/insights")
async def get_insights(user_id: str = "00000000-0000-0000-0000-000000000001"):
    """Returns real user health data for the Insights dashboard."""
    print("--- INSIGHTS REQUEST ---")
    try:
        user_state = get_twin_state(user_id)
        user_history = get_user_history(user_id)
        
        # Calculate risk scores
        age = user_state.get("age", 22)
        gender = user_state.get("gender", "male")
        active = user_state.get("physically_active", False)
        smoker = user_state.get("smoker", False)
        bmi = user_state.get("bmi", 22)
        sbp = user_state.get("sbp", 130)
        total_chol = user_state.get("total_chol", 180)
        hdl = user_state.get("hdl", 45)
        on_bp_meds = user_state.get("on_bp_meds", False)
        family_hx = user_state.get("family_hx_diabetes", False)
        hypertension = user_state.get("hypertension", False)
        
        cvd_risk = calculate_framingham_risk_proper(gender, age, total_chol, hdl, sbp, on_bp_meds, smoker)
        diabetes_risk = calculate_ada_risk_score(age, gender, False, family_hx, hypertension, active, bmi)
        
        # Get daily logs breakdown
        recent_logs = user_history.get("recent_logs", [])
        meal_count = sum(1 for log in recent_logs if "[meal]" in log.lower())
        exercise_count = sum(1 for log in recent_logs if "[exercise]" in log.lower())
        
        # Blood pressure status
        bp_status = "Normal" if sbp < 120 else ("Elevated" if sbp < 130 else ("High Stage 1" if sbp < 140 else "High Stage 2"))
        
        return {
            "user": {
                "name": user_state.get("name", "User"),
                "age": age,
                "gender": gender,
                "bmi": bmi,
                "smoker": smoker,
                "physically_active": active,
            },
            "risk_scores": {
                "cvd": cvd_risk,
                "diabetes": diabetes_risk[1],
                "diabetes_high_risk": diabetes_risk[0],
            },
            "vitals": {
                "sbp": sbp,
                "dbp": 76,
                "bp_status": bp_status,
                "heart_rate": 72,
                "resting_hr": 68,
                "total_chol": total_chol,
                "hdl": hdl,
            },
            "activity": {
                "steps": 8432 if active else 4200,
                "goal": 10000,
                "exercise_sessions": exercise_count,
            },
            "nutrition": {
                "meals_logged": meal_count,
                "protein": 120,
                "carbs": 250,
                "fats": 65,
            },
            "sleep": {
                "hours": 7.2,
                "trend": [6.5, 7.0, 6.8, 7.2, 7.5, 7.1, 7.2],
            },
            "stress": {
                "hrv": 65,
                "level": "Moderate",
            },
            "behavioral_facts": user_history.get("behavioral_facts", []),
            "recent_logs": recent_logs,
        }
    except Exception as e:
        print(f"Insights error: {e}")
        return {"error": "Failed to fetch insights", "details": str(e)}

@app.get("/api/user/ai-summary")
async def get_ai_summary(user_id: str = "00000000-0000-0000-0000-000000000001"):
    """Generates an AI-powered narrative summary from conversation history."""
    print("--- AI SUMMARY REQUEST ---")
    try:
        # Fetch conversation history
        conversations = get_conversation_history(user_id, limit=100)
        
        if not conversations:
            return {"summary": "No conversation history available yet."}
        
        # Build conversation transcript
        transcript = ""
        for conv in reversed(conversations):  # Oldest first
            role = conv.get("role", "unknown")
            content = conv.get("content", "")
            transcript += f"{role}: {content}\n"
        
        # Generate AI summary
        summary_prompt = f"""Analyze the following health-related conversation history and generate a patient health record summary.

Conversation History:
{transcript}

Your summary should include ONLY the following sections:
1. **Health Issues & Symptoms**: What health problems, symptoms, or concerns has the patient mentioned?
2. **Lifestyle Patterns**: What habits (diet, exercise, sleep, smoking, alcohol, etc.) has the patient discussed?
3. **Risk Factors**: What risk factors have been identified from the conversation?
4. **Medications & Treatments**: Any medications or treatments mentioned by the patient?
5. **Family History**: Any family health history mentioned?

DO NOT include:
- AI advice or recommendations
- Action items or to-do lists
- Suggestions for improvement
- Future goals or plans

Format the summary as a clear, professional patient health record suitable for a healthcare provider.

Return the summary in plain text, well-structured with headings."""

        response = client.chat.completions.create(
            messages=[{"role": "user", "content": summary_prompt}],
            model="llama-3.3-70b-versatile"
        )
        
        summary = response.choices[0].message.content
        
        return {
            "summary": summary,
            "conversation_count": len(conversations),
            "generated_at": "now"
        }
    except Exception as e:
        print(f"AI Summary error: {e}")
        return {"error": "Failed to generate summary", "details": str(e)}

# --- 6. MANUAL TEST BLOCK (Commented Out) ---
#if __name__ == "__main__":
    # This only runs if you type 'python main.py'
    #print("--- RUNNING MANUAL GRAPH TEST ---")
    #test_state = {"user_message": "i feel tired can you check my sleep data?."}
    #result = twin_brain.invoke(test_state)
    #print("Final AI Reply:", result["ai_final_reply"])
 #   test_state = {"user_message": "i feel tired can you check my sleep data?."}
 #   result = twin_brain.invoke(test_state)
  #  print("Final AI Reply:", result["ai_final_reply"])

@app.get("/api/wearable/authorize")
async def authorize_wearable(user_id: str = "00000000-0000-0000-0000-000000000001"):
    """Generate Google OAuth authorization URL."""
    print("--- WEARABLE AUTHORIZATION REQUEST ---")
    try:
        auth_url = get_auth_url(user_id)
        return {"auth_url": auth_url}
    except Exception as e:
        print(f"Authorization error: {e}")
        return {"error": "Failed to generate authorization URL", "details": str(e)}
 
@app.post("/api/wearable/callback")
async def wearable_callback(payload: dict):
    """Exchange authorization code for tokens."""
    print("--- WEARABLE CALLBACK REQUEST ---")
    try:
        code = payload.get("code")
        user_id = payload.get("user_id", "00000000-0000-0000-0000-000000000001")
        
        result = exchange_code_for_tokens(code, user_id)
        return result
    except Exception as e:
        print(f"Callback error: {e}")
        return {"error": "Failed to exchange code for tokens", "details": str(e)}
 
@app.post("/api/wearable/sync")
async def sync_wearable_data(payload: dict):
    """Sync data from Google Fit."""
    print("--- WEARABLE SYNC REQUEST ---")
    try:
        user_id = payload.get("user_id", "00000000-0000-0000-0000-000000000001")
        result = sync_all_data(user_id)
        return result
    except Exception as e:
        print(f"Sync error: {e}")
        return {"error": "Failed to sync wearable data", "details": str(e)}
 
@app.get("/api/wearable/data")
async def get_wearable_data_endpoint(
    user_id: str = "00000000-0000-0000-0000-000000000001",
    data_type: str = None,
    days: int = 7
):
    """Get stored wearable data."""
    print("--- WEARABLE DATA REQUEST ---")
    try:
        data = get_wearable_data(user_id, data_type, days)
        return {"data": data}
    except Exception as e:
        print(f"Data fetch error: {e}")
        return {"error": "Failed to fetch wearable data", "details": str(e)}
 
@app.get("/api/wearable/status")
async def get_wearable_status(user_id: str = "00000000-0000-0000-0000-000000000001"):
    """Check wearable connection status."""
    print("--- WEARABLE STATUS REQUEST ---")
    try:
        status = get_wearable_connection_status(user_id)
        return status
    except Exception as e:
        print(f"Status check error: {e}")
        return {"error": "Failed to check status", "details": str(e)}

@app.delete("/api/wearable/disconnect")
async def disconnect_wearable(user_id: str = "00000000-0000-0000-0000-000000000001"):
    """Disconnect wearable by deleting tokens and data."""
    print("--- WEARABLE DISCONNECT REQUEST ---")
    try:
        supabase.table("wearable_tokens").delete().eq("user_id", user_id).execute()
        supabase.table("wearable_data").delete().eq("user_id", user_id).execute()
        return {"success": True, "message": "Disconnected successfully"}
    except Exception as e:
        print(f"Disconnect error: {e}")
        return {"error": "Failed to disconnect", "details": str(e)}

@app.get("/api/chat/history")
async def get_chat_history(user_id: str = "00000000-0000-0000-0000-000000000001"):
    """Fetch chat history from database."""
    print("--- CHAT HISTORY REQUEST ---")
    try:
        history = get_conversation_history(user_id)
        return {"history": history}
    except Exception as e:
        print(f"Chat history error: {e}")
        return {"error": "Failed to fetch chat history", "details": str(e)}

@app.post("/api/health-log")
async def log_health_data(user_id: str, data_type: str, value: str = ""):
    """Save manually logged health data from chat to wearable_data table."""
    print(f"--- HEALTH LOG REQUEST --- user: {user_id}, type: {data_type}")
    try:
        import json
        parsed_value = json.loads(value) if isinstance(value, str) and value.startswith('{') else {"value": value}
        result = save_manual_health_data(user_id, data_type, parsed_value)
        return {"success": True, "data": result}
    except Exception as e:
        print(f"Health log error: {e}")
        return {"error": "Failed to log health data", "details": str(e)}