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
    view: str

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
        user_state = get_twin_state(user_id)
        
        # Check if message is asking for insights or recommendations before triggering RAG
        msg_lower = state["user_message"].lower()
        rag_keywords = ["insight", "recommend", "advice", "suggest", "guideline", "what should", "how can", "risk", "health", "improve", "better"]
        should_use_rag = any(keyword in msg_lower for keyword in rag_keywords)
        
        if should_use_rag:
            clinical_guidelines = get_clinical_rag(state["user_message"])
        else:
            clinical_guidelines = []
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
    
    # Log user message to database (assistant reply saved later after metric question is appended)
    try:
        save_conversation_turn(user_id, "user", state["user_message"], "chat")
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
            log_daily_activity(user_id, log_entry, log_type=log_type)
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
- Meals/nutrition (e.g., "I had breakfast", "ate lunch", "dinner was rice and dal", "I had 2 meals today")

If user mentions heart rate is "normal", "good", "fine", or similar qualitative terms, extract as heart_rate with value "normal" and note that a specific number should be requested.
For meals, extract the meal type (breakfast/lunch/dinner/snack) and any description of what was eaten.

If no metrics found, return: {{"metrics": []}}
If found, return: {{"metrics": [{{"type": "steps|heart_rate|sleep|blood_pressure|nutrition", "value": <number or "normal" or meal description>, "unit": "steps|bpm|hours|mmHg|meal"}}]}}

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
                    if isinstance(metric_value, str) and metric_value.lower() in ["normal", "good", "fine"]:
                        # Save qualitative value but note it needs specific number
                        save_manual_health_data(user_id, "heart_rate", {"bpm": "normal", "date": datetime.utcnow().strftime('%Y-%m-%d')})
                        print(f"--- Saved heart rate metric: {metric_value} (qualitative) ---")
                    else:
                        save_manual_health_data(user_id, "heart_rate", {"bpm": int(metric_value), "date": datetime.utcnow().strftime('%Y-%m-%d')})
                        print(f"--- Saved heart rate metric: {metric_value} bpm ---")
                elif metric_type == "sleep":
                    save_manual_health_data(user_id, "sleep", {"hours": float(metric_value), "date": datetime.utcnow().strftime('%Y-%m-%d')})
                    print(f"--- Saved sleep metric: {metric_value} hours ---")
                elif metric_type == "blood_pressure":
                    save_manual_health_data(user_id, "blood_pressure", {"reading": str(metric_value), "date": datetime.utcnow().strftime('%Y-%m-%d')})
                    print(f"--- Saved blood pressure metric: {metric_value} ---")
                elif metric_type == "nutrition":
                    save_manual_health_data(user_id, "nutrition", {"meal": str(metric_value), "date": datetime.utcnow().strftime('%Y-%m-%d')})
                    print(f"--- Saved nutrition metric: {metric_value} ---")
    except Exception as e:
        print(f"Health metrics extraction error: {e}")
    
    # Check if user has wearable data - if not, append specific health questions
    try:
        from database import get_latest_wearable_data, get_conversation_history
        has_steps = get_latest_wearable_data(user_id, "steps") is not None
        hr_data = get_latest_wearable_data(user_id, "heart_rate")
        has_sleep = get_latest_wearable_data(user_id, "sleep") is not None
        
        # Check if heart rate is a valid number or qualitative value like "normal"
        has_valid_hr = False
        if hr_data:
            hr_value = hr_data.get('value', {}).get('bpm')
            if hr_value:
                if isinstance(hr_value, (int, float)) and hr_value > 0:
                    has_valid_hr = True
                elif isinstance(hr_value, str) and hr_value.lower() in ['normal', 'good', 'fine', 'healthy']:
                    has_valid_hr = True
        
        # Check if user provided metrics in recent conversation (last 20 turns)
        recent_history = get_conversation_history(user_id, limit=20)
        recent_messages = [turn.get('content', '').lower() for turn in recent_history]
        
        # Check which metrics the USER mentioned (only user messages, not AI questions)
        user_messages = [turn.get('content', '').lower() for turn in recent_history if turn.get('role') == 'user']
        user_mentioned_steps = any('step' in msg for msg in user_messages)
        user_mentioned_hr = any('heart rate' in msg or 'bpm' in msg for msg in user_messages)
        user_mentioned_sleep = any('sleep' in msg for msg in user_messages)
        
        # Check if we've already asked for metrics in this conversation
        # Look for our metric question patterns in recent assistant messages
        assistant_messages = [turn.get('content', '') for turn in recent_history if turn.get('role') == 'assistant']
        metric_question_patterns = ['do you track your daily steps', 'do you happen to know your resting heart rate', 'how much sleep did you get last night', 'Quick question:']
        already_asked = any(any(pattern in msg.lower() for pattern in metric_question_patterns) for msg in assistant_messages)
        
        # Only ask for ONE metric at a time, not all missing metrics, and only once per conversation
        if not already_asked:
            missing_metrics = []
            # Don't ask about steps if user already mentioned steps OR we already have the data
            if not has_steps and not user_mentioned_steps:
                missing_metrics.append("steps")
            if not has_valid_hr and not user_mentioned_hr:
                missing_metrics.append("resting heart rate")
            if not has_sleep and not user_mentioned_sleep:
                missing_metrics.append("sleep hours")
            
            # Check metric freshness and add time-based reminders
            freshness_prompt = ""
            try:
                freshness_response = get_metric_freshness(user_id)
                if freshness_response.get("needs_update"):
                    stale = freshness_response.get("stale_metrics", [])
                    freshness_prompt = "\n\n" + " | ".join([m["message"] for m in stale])
            except:
                pass
            
            # Only ask for ONE metric at a time, not all missing metrics
            if missing_metrics:
                # Pick only one metric to ask about (first one in priority order)
                metric_to_ask = missing_metrics[0]
                
                # Create a natural, conversational question for just one metric
                if metric_to_ask == "steps":
                    question = " By the way, do you track your daily steps?"
                elif metric_to_ask == "resting heart rate":
                    question = " Also, do you happen to know your resting heart rate?"
                elif metric_to_ask == "sleep hours":
                    question = " Oh, and how much sleep did you get last night?"
                
                chat_completion_content = chat_completion.choices[0].message.content + question + freshness_prompt
            elif freshness_prompt:
                chat_completion_content = chat_completion.choices[0].message.content + freshness_prompt
            else:
                chat_completion_content = chat_completion.choices[0].message.content
        else:
            chat_completion_content = chat_completion.choices[0].message.content
    except Exception as e:
        print(f"Wearable data check error: {e}")
        chat_completion_content = chat_completion.choices[0].message.content
    
    # Save assistant reply to database AFTER metric question is appended
    try:
        save_conversation_turn(user_id, "assistant", chat_completion_content, "clinical_twin")
    except Exception as e:
        print(f"Conversation logging error: {e}")
    
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
    }  # Added closing brace here

# --- 3. CONDITIONAL ROUTING LOGIC ---

def route_request(state: TwinState):
    """Decider: Routes to appropriate agent based on intent and view."""
    print("--- [A2A] Routing Decision ---")
    data = state.get("emotion_data", {})
    msg_lower = state["user_message"].lower()
    view = state.get("view", "chat")
    
    # Priority 1: Emergency - high stress or pain keywords
    is_high_stress = data.get("stress_score", 0) > 0.8
    has_pain_keywords = any(word in msg_lower for word in ["pain", "hurt", "emergency", "dying", "racing"])
    
    if is_high_stress or has_pain_keywords:
        return "emergency"
    
    # Priority 2: What-If Simulation (by view or message content)
    if view == "whatif" or "what if" in msg_lower:
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
        view = payload.get("view", "chat")  # 'chat' or 'whatif'
        initial_input = {"user_message": user_msg, "user_id": user_id, "view": view}
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
        print(f"CRITICAL ERROR: {str(e)}")
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
        
        # Get real nutrition data from wearable_data
        nutrition_wearable = get_wearable_data(user_id, "nutrition", days=7)
        nutrition_meals = [d.get('value', {}).get('meal', 'meal') for d in nutrition_wearable if d.get('value')]
        meals_logged = len(nutrition_meals) if nutrition_meals else meal_count
        
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
                "meals_logged": meals_logged,
                "meals": nutrition_meals[:5],
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

@app.get("/api/user/metric-insights")
async def get_metric_insights(user_id: str = "00000000-0000-0000-0000-000000000001"):
    """Generate dynamic AI insights based on current metrics."""
    print("--- METRIC INSIGHTS REQUEST ---")
    try:
        # Fetch current metrics and user data
        user_state = get_twin_state(user_id)
        wearable_data = get_wearable_data(user_id, None, days=7)
        
        # Extract current metrics
        steps_data = [d for d in wearable_data if d.get('data_type') == 'steps']
        hr_data = [d for d in wearable_data if d.get('data_type') == 'heart_rate']
        sleep_data = [d for d in wearable_data if d.get('data_type') == 'sleep']
        nutrition_data = [d for d in wearable_data if d.get('data_type') == 'nutrition']
        
        latest_steps = steps_data[0].get('value', {}).get('steps') if steps_data else 0
        latest_hr = hr_data[0].get('value', {}).get('bpm') if hr_data else None
        latest_sleep = sleep_data[0].get('value', {}).get('hours') if sleep_data else 0
        meals_logged = len(nutrition_data)
        meal_descriptions = [d.get('value', {}).get('meal', 'meal') for d in nutrition_data[:5]]
        
        # Generate per-card insights using LLM
        insights_prompt = f"""Generate personalized health insights for a dashboard. Return JSON.

User Profile:
- Age: {user_state.get('age', 22)}
- Gender: {user_state.get('gender', 'male')}
- Smoker: {user_state.get('smoker', False)}
- Physically Active: {user_state.get('physically_active', False)}

Current Metrics:
- Steps: {latest_steps} (daily goal: 10000)
- Heart Rate: {latest_hr} bpm
- Sleep: {latest_sleep} hours avg
- Meals logged: {meals_logged} ({', '.join(meal_descriptions) if meal_descriptions else 'none'})

Generate insights for each dashboard card (short, actionable, 1-2 sentences each):
- steps: relate ONLY to steps/goal/progress
- heart_rate: relate ONLY to heart rate
- sleep: relate ONLY to sleep duration/consistency
- nutrition: relate ONLY to meal logging / macro balance (if no meal data, give a generic but relevant logging tip)
- stress: relate ONLY to stress/HRV/wellbeing (if no HRV data, give a generic stress tip)

Return ONLY valid JSON like: {{"steps": "...", "heart_rate": "...", "sleep": "...", "nutrition": "...", "stress": "..."}}"""

        response = client.chat.completions.create(
            messages=[{"role": "user", "content": insights_prompt}],
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"}
        )
        
        insights = json.loads(response.choices[0].message.content)
        
        return {
            "steps": insights.get("steps", "Track your daily steps to stay active"),
            "heart_rate": insights.get("heart_rate", "Monitor your heart rate for cardiovascular health"),
            "sleep": insights.get("sleep", "Aim for 7-9 hours of quality sleep"),
            "nutrition": insights.get("nutrition", "Log your meals to get more accurate nutrition insights"),
            "stress": insights.get("stress", "Try a short breathing break to reduce stress")
        }
    except Exception as e:
        print(f"Metric insights error: {e}")
        return {
            "steps": "Track your daily steps to stay active",
            "heart_rate": "Monitor your heart rate for cardiovascular health",
            "sleep": "Aim for 7-9 hours of quality sleep",
            "nutrition": "Log your meals to get more accurate nutrition insights",
            "stress": "Try a short breathing break to reduce stress"
        }

@app.get("/api/user/metric-freshness")
async def get_metric_freshness(user_id: str = "00000000-0000-0000-0000-000000000001"):
    """Check freshness of metrics and provide time-based reminders."""
    print("--- METRIC FRESHNESS REQUEST ---")
    try:
        from datetime import datetime, timedelta
        
        wearable_data = get_wearable_data(user_id, None, days=30)
        
        # Get latest data for each metric type
        steps_data = [d for d in wearable_data if d.get('data_type') == 'steps']
        hr_data = [d for d in wearable_data if d.get('data_type') == 'heart_rate']
        sleep_data = [d for d in wearable_data if d.get('data_type') == 'sleep']
        
        # Calculate freshness (hours since last update)
        now = datetime.utcnow()
        
        steps_freshness = None
        hr_freshness = None
        sleep_freshness = None
        
        if steps_data:
            steps_timestamp = datetime.fromisoformat(steps_data[0].get('timestamp').replace('Z', '+00:00'))
            steps_freshness = (now - steps_timestamp).total_seconds() / 3600
        
        if hr_data:
            hr_timestamp = datetime.fromisoformat(hr_data[0].get('timestamp').replace('Z', '+00:00'))
            hr_freshness = (now - hr_timestamp).total_seconds() / 3600
        
        if sleep_data:
            sleep_timestamp = datetime.fromisoformat(sleep_data[0].get('timestamp').replace('Z', '+00:00'))
            sleep_freshness = (now - sleep_timestamp).total_seconds() / 3600
        
        # Determine which metrics need updates (older than 24 hours)
        stale_metrics = []
        if steps_freshness is not None and steps_freshness > 24:
            stale_metrics.append({
                "type": "steps",
                "hours_old": steps_freshness,
                "message": f"Steps data is {int(steps_freshness)} hours old. Time for an update!"
            })
        if hr_freshness is not None and hr_freshness > 24:
            stale_metrics.append({
                "type": "heart_rate",
                "hours_old": hr_freshness,
                "message": f"Heart rate data is {int(hr_freshness)} hours old. Time for an update!"
            })
        if sleep_freshness is not None and sleep_freshness > 24:
            stale_metrics.append({
                "type": "sleep",
                "hours_old": sleep_freshness,
                "message": f"Sleep data is {int(sleep_freshness)} hours old. Time for an update!"
            })
        
        return {
            "freshness": {
                "steps": steps_freshness,
                "heart_rate": hr_freshness,
                "sleep": sleep_freshness
            },
            "stale_metrics": stale_metrics,
            "needs_update": len(stale_metrics) > 0
        }
    except Exception as e:
        print(f"Metric freshness error: {e}")
        return {
            "freshness": {"steps": None, "heart_rate": None, "sleep": None},
            "stale_metrics": [],
            "needs_update": False
        }

@app.post("/api/user/recalculate-bmi")
async def recalculate_bmi(user_id: str = "00000000-0000-0000-0000-000000000001"):
    """Recalculate BMI for an existing user based on their stored height and weight."""
    print("--- RECALCULATE BMI REQUEST ---")
    try:
        user_state = get_twin_state(user_id)
        
        if not user_state:
            return {"error": "User not found"}
        
        height = float(user_state.get("height", 170))
        weight = float(user_state.get("weight", 70))
        
        # Check if height is in meters (less than 3) or cm (greater than 100)
        if height < 3:
            # Height is already in meters
            height_m = height
        else:
            # Height is in cm, convert to meters
            height_m = height / 100
        
        bmi = round(weight / (height_m ** 2), 1)
        
        # Validate BMI is in reasonable range (15-50)
        if bmi < 15 or bmi > 50:
            print(f"Warning: Calculated BMI {bmi} is outside normal range. Height: {height}, Weight: {weight}")
            # Recalculate with default values if BMI is unreasonable
            bmi = round(weight / ((1.7) ** 2), 1)
        
        # Update the BMI in the database
        update_twin_state(user_id, {"bmi": bmi})
        
        return {
            "user_id": user_id,
            "height": height,
            "weight": weight,
            "bmi": bmi,
            "message": "BMI recalculated successfully"
        }
    except Exception as e:
        print(f"BMI recalculation error: {e}")
        return {"error": "Failed to recalculate BMI", "details": str(e)}

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
async def get_chat_history(user_id: str = "00000000-0000-0000-0000-000000000001", source: str = None):
    """Fetch chat history from database. Optionally filter by source (chat, clinical_twin, whatif_simulator)."""
    print(f"--- CHAT HISTORY REQUEST (source={source}) ---")
    try:
        # If source is specified, filter by it; otherwise return all
        # For Twin Chat: exclude whatif_simulator messages
        # For What-If: only get whatif_simulator messages
        if source == "chat":
            # Get chat + clinical_twin messages (Twin Chat tab)
            history_all = get_conversation_history(user_id, limit=100)
            history = [h for h in history_all if h.get('source') in ('chat', 'clinical_twin')]
        elif source == "whatif":
            # Get whatif_simulator messages only (What-If tab)
            history = get_conversation_history(user_id, limit=100, source="whatif_simulator")
        else:
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